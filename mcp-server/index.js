#!/usr/bin/env node
/**
 * Zero-Scan MCP Server (Node.js implementation)
 * Model Context Protocol (MCP) Server for Zero-Scan Context Engine (.agent/ Project Memory).
 * Zero external dependencies (pure Node.js 18+ standard library).
 * 
 * Copyright (c) 2026 Chau Vu / CPF-FAMILY. Licensed under MIT.
 */

const fs = require('fs');
const path = require('path');
const readline = require('readline');
const { execSync } = require('child_process');

const SERVER_NAME = 'zeroscan-mcp';
const SERVER_VERSION = '2.0.0';
const PROTOCOL_VERSION = '2024-11-05';
const MAX_BOOTSTRAP_CONTEXT_BYTES = 10 * 1024; // 10 KB budget

function findAgentDir(startPath) {
    let current = path.resolve(startPath || process.cwd());
    while (true) {
        const candidate = path.join(current, '.agent');
        if (fs.existsSync(candidate) && fs.statSync(candidate).isDirectory()) {
            return candidate;
        }
        const parent = path.dirname(current);
        if (parent === current) break;
        current = parent;
    }
    return path.join(process.cwd(), '.agent');
}

function getGitCommit(cwd) {
    try {
        return execSync('git rev-parse HEAD', { cwd, encoding: 'utf8' }).trim();
    } catch {
        return 'uncommitted';
    }
}

const TOOLS = [
    {
        name: 'zeroscan_boot',
        description: 'Read the Level 0 Boot Anchor (.agent/BOOT.md) instantly (< 1 KB / ~500 tokens). Eliminates directory scanning overhead and provides immediate architectural orientation.',
        inputSchema: {
            type: 'object',
            properties: {
                project_path: {
                    type: 'string',
                    description: 'Optional root directory path of the repository.'
                }
            }
        }
    },
    {
        name: 'zeroscan_get_map',
        description: 'Retrieve the structured GPS domain map (.agent/PROJECT_MAP.json). Shows domain modules, critical files, entry points, and test suites without directory crawling.',
        inputSchema: {
            type: 'object',
            properties: {
                project_path: {
                    type: 'string',
                    description: 'Optional root directory path of the repository.'
                }
            }
        }
    },
    {
        name: 'zeroscan_get_state',
        description: 'Retrieve project progress, completed milestones, git hash, and active branch state (.agent/PROJECT_STATE.json).',
        inputSchema: {
            type: 'object',
            properties: {
                project_path: {
                    type: 'string',
                    description: 'Optional root directory path of the repository.'
                }
            }
        }
    },
    {
        name: 'zeroscan_get_next_task',
        description: 'Read the immediate next task and atomic execution steps from .agent/NEXT_TASK.md.',
        inputSchema: {
            type: 'object',
            properties: {
                project_path: {
                    type: 'string',
                    description: 'Optional root directory path of the repository.'
                }
            }
        }
    },
    {
        name: 'zeroscan_record_decision',
        description: 'Append an Architectural Decision Record (ADR) into .agent/DECISIONS.md to preserve architectural consensus across AI agent sessions.',
        inputSchema: {
            type: 'object',
            properties: {
                title: { type: 'string', description: 'Brief title of the architectural decision.' },
                decision: { type: 'string', description: 'Details of the decision, rationale, and consequences.' },
                author: { type: 'string', description: 'Author or Agent identifier.' },
                project_path: { type: 'string', description: 'Optional root directory path of the repository.' }
            },
            required: ['title', 'decision']
        }
    },
    {
        name: 'zeroscan_validate',
        description: 'Validate that the repository .agent/ directory conforms to the Zero-Scan specification and stays strictly within the <= 10 KB context budget.',
        inputSchema: {
            type: 'object',
            properties: {
                project_path: {
                    type: 'string',
                    description: 'Optional root directory path of the repository.'
                }
            }
        }
    }
];

function handleInitialize(params) {
    return {
        protocolVersion: PROTOCOL_VERSION,
        capabilities: {
            tools: { listChanged: false },
            prompts: { listChanged: false }
        },
        serverInfo: {
            name: SERVER_NAME,
            version: SERVER_VERSION
        }
    };
}

function handleToolsList() {
    return { tools: TOOLS };
}

function handleToolsCall(name, args = {}) {
    const projectPath = path.resolve(args.project_path || '.');
    const agentDir = findAgentDir(projectPath);

    if (name === 'zeroscan_boot') {
        const bootFile = path.join(agentDir, 'BOOT.md');
        if (!fs.existsSync(bootFile)) {
            return {
                content: [{ type: 'text', text: `Error: No .agent/BOOT.md found at ${agentDir}. Initialize with zeroscan bootstrap first.` }],
                isError: true
            };
        }
        const content = fs.readFileSync(bootFile, 'utf8');
        const sizeBytes = Buffer.byteLength(content, 'utf8');
        return {
            content: [{ type: 'text', text: `# Zero-Scan Boot Anchor (${sizeBytes} bytes)\n\n${content}` }]
        };
    }

    if (name === 'zeroscan_get_map') {
        const mapFile = path.join(agentDir, 'PROJECT_MAP.json');
        if (!fs.existsSync(mapFile)) {
            return { content: [{ type: 'text', text: `Error: No .agent/PROJECT_MAP.json found at ${agentDir}.` }], isError: true };
        }
        return { content: [{ type: 'text', text: fs.readFileSync(mapFile, 'utf8') }] };
    }

    if (name === 'zeroscan_get_state') {
        const stateFile = path.join(agentDir, 'PROJECT_STATE.json');
        if (!fs.existsSync(stateFile)) {
            return { content: [{ type: 'text', text: `Error: No .agent/PROJECT_STATE.json found at ${agentDir}.` }], isError: true };
        }
        return { content: [{ type: 'text', text: fs.readFileSync(stateFile, 'utf8') }] };
    }

    if (name === 'zeroscan_get_next_task') {
        const taskFile = path.join(agentDir, 'NEXT_TASK.md');
        if (!fs.existsSync(taskFile)) {
            return { content: [{ type: 'text', text: `Error: No .agent/NEXT_TASK.md found at ${agentDir}.` }], isError: true };
        }
        return { content: [{ type: 'text', text: fs.readFileSync(taskFile, 'utf8') }] };
    }

    if (name === 'zeroscan_record_decision') {
        const decFile = path.join(agentDir, 'DECISIONS.md');
        if (!fs.existsSync(decFile)) {
            return { content: [{ type: 'text', text: `Error: No .agent/DECISIONS.md found at ${agentDir}.` }], isError: true };
        }
        const { title, decision, author = 'AI Agent' } = args;
        const dateStr = new Date().toISOString().split('T')[0];
        const gitHash = getGitCommit(projectPath).substring(0, 7);
        const entry = `\n\n### ADR: ${title} (${dateStr})\n- **Author:** ${author}\n- **Git Commit:** \`${gitHash}\`\n- **Decision:**\n${decision}\n`;
        fs.appendFileSync(decFile, entry, 'utf8');
        return { content: [{ type: 'text', text: `Successfully appended ADR '${title}' to ${decFile}.` }] };
    }

    if (name === 'zeroscan_validate') {
        const requiredFiles = ['BOOT.md', 'PROJECT_STATE.json', 'PROJECT_MAP.json', 'DECISIONS.md', 'NEXT_TASK.md'];
        const missing = [];
        let totalBytes = 0;

        for (const rf of requiredFiles) {
            const fp = path.join(agentDir, rf);
            if (!fs.existsSync(fp)) {
                missing.push(rf);
            } else {
                totalBytes += fs.statSync(fp).size;
            }
        }

        const isValid = missing.length === 0 && totalBytes <= MAX_BOOTSTRAP_CONTEXT_BYTES;
        const statusText = `Zero-Scan Specification Validation:\n- Status: ${isValid ? 'PASS ✅' : 'FAIL ❌'}\n- Total Context Size: ${totalBytes} / ${MAX_BOOTSTRAP_CONTEXT_BYTES} bytes (Budget: <= 10 KB)\n- Missing Files: ${missing.length ? missing.join(', ') : 'None'}\n- Location: ${agentDir}`;
        return { content: [{ type: 'text', text: statusText }], isError: !isValid };
    }

    throw new Error(`Unknown tool: ${name}`);
}

function runStdioServer() {
    const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout,
        terminal: false
    });

    rl.on('line', (line) => {
        line = line.trim();
        if (!line) return;

        let reqId = null;
        try {
            const request = JSON.parse(line);
            reqId = request.id;
            const method = request.method;
            const params = request.params || {};

            let response;
            if (method === 'initialize') {
                response = { jsonrpc: '2.0', id: reqId, result: handleInitialize(params) };
            } else if (method === 'notifications/initialized') {
                return;
            } else if (method === 'tools/list') {
                response = { jsonrpc: '2.0', id: reqId, result: handleToolsList() };
            } else if (method === 'tools/call') {
                response = { jsonrpc: '2.0', id: reqId, result: handleToolsCall(params.name, params.arguments) };
            } else if (method === 'ping') {
                response = { jsonrpc: '2.0', id: reqId, result: {} };
            } else {
                response = { jsonrpc: '2.0', id: reqId, error: { code: -32601, message: `Method not found: ${method}` } };
            }

            process.stdout.write(JSON.stringify(response) + '\n');
        } catch (err) {
            const errResponse = { jsonrpc: '2.0', id: reqId, error: { code: -32603, message: err.message } };
            process.stdout.write(JSON.stringify(errResponse) + '\n');
        }
    });
}

if (require.main === module) {
    runStdioServer();
}

module.exports = {
    findAgentDir,
    TOOLS,
    handleInitialize,
    handleToolsList,
    handleToolsCall,
    runStdioServer
};
