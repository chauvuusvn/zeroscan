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
const SERVER_VERSION = '2.2.0';
const PROTOCOL_VERSION = '2024-11-05';
const MAX_BOOTSTRAP_CONTEXT_BYTES = 10 * 1024; // 10 KB budget ceiling

function getDefaultWorkspaceRoot() {
    const envRoot = process.env.ZEROSCAN_PROJECT_ROOT || process.env.WORKSPACE_FOLDER;
    if (envRoot && fs.existsSync(envRoot) && fs.statSync(envRoot).isDirectory()) {
        return path.resolve(envRoot);
    }
    return process.cwd();
}

function findAgentDir(startPath) {
    const defaultRoot = getDefaultWorkspaceRoot();
    let current = path.resolve(startPath || defaultRoot);
    while (true) {
        const candidate = path.join(current, '.agent');
        if (fs.existsSync(candidate) && fs.statSync(candidate).isDirectory()) {
            return candidate;
        }
        const parent = path.dirname(current);
        if (parent === current) break;
        current = parent;
    }
    return path.join(defaultRoot, '.agent');
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
        description: 'Get architectural GPS mapping (.agent/PROJECT_MAP.json) to locate exact domain files, entry points, and test suites.',
        inputSchema: {
            type: 'object',
            properties: {
                domain: {
                    type: 'string',
                    description: 'Optional functional domain filter (e.g. core, auth, api, db).'
                },
                project_path: {
                    type: 'string',
                    description: 'Optional root directory path of the repository.'
                }
            }
        }
    },
    {
        name: 'zeroscan_read_state',
        description: 'Read the full project state machine (.agent/PROJECT_STATE.json), current phase, verified commit, and context metrics.',
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
        name: 'zeroscan_read_decisions',
        description: 'Read locked Architectural Decision Records (.agent/DECISIONS.md) to understand non-negotiable architectural constraints.',
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
        name: 'zeroscan_read_next_task',
        description: 'Read the active task specification (.agent/NEXT_TASK.md), domains, and acceptance criteria.',
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
        description: 'Append a newly approved Architectural Decision Record (ADR) to .agent/DECISIONS.md.',
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

const PROMPTS = [
    {
        name: 'zeroscan_boot_prompt',
        description: 'System prompt template to ground an AI agent instantly using Zero-Scan Level 0 Boot Anchor without scanning the repository.',
        arguments: [
            {
                name: 'project_path',
                description: 'Path to repository root (defaults to current working directory)',
                required: false
            }
        ]
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

function handlePromptsList() {
    return { prompts: PROMPTS };
}

function handlePromptsGet(name, args = {}) {
    if (name === 'zeroscan_boot_prompt') {
        const projectPath = path.resolve(args.project_path || '.');
        const agentDir = findAgentDir(projectPath);
        const bootFile = path.join(agentDir, 'BOOT.md');
        const taskFile = path.join(agentDir, 'NEXT_TASK.md');

        let bootContent = fs.existsSync(bootFile) ? fs.readFileSync(bootFile, 'utf8') : 'No .agent/BOOT.md found.';
        let taskContent = fs.existsSync(taskFile) ? fs.readFileSync(taskFile, 'utf8') : 'No active task found.';

        return {
            description: 'Zero-Scan Level 0 Agent Grounding Prompt',
            messages: [
                {
                    role: 'user',
                    content: {
                        type: 'text',
                        text: `You are an AI Coding Agent operating under Zero-Scan Project Memory V2.2.0.\n\n=== LEVEL 0 BOOT ANCHOR ===\n${bootContent}\n\n=== CURRENT NEXT TASK ===\n${taskContent}\n\nDo NOT scan the full repository. Proceed with your task directly using this grounded context.`
                    }
                }
            ]
        };
    }
    throw new Error(`Unknown prompt: ${name}`);
}

function resolveSafeProjectPath(rawPath, rootBoundary) {
    const boundary = path.resolve(rootBoundary || getDefaultWorkspaceRoot());
    if (!rawPath) return boundary;
    try {
        const candidate = path.resolve(rawPath);
        const rel = path.relative(boundary, candidate);
        // Ensure candidate is inside boundary (no leading .. and not an absolute external path)
        if (!rel.startsWith('..') && !path.isAbsolute(rel) && fs.existsSync(candidate) && fs.statSync(candidate).isDirectory()) {
            return candidate;
        }
        if (fs.existsSync(candidate) && fs.statSync(candidate).isDirectory()) {
            return candidate;
        }
    } catch {}
    return boundary;
}

function handleToolsCall(name, args = {}) {
    const projectPath = resolveSafeProjectPath(args.project_path);
    const agentDir = findAgentDir(projectPath);

    if (name === 'zeroscan_boot') {
        const bootFile = path.join(agentDir, 'BOOT.md');
        if (!fs.existsSync(bootFile)) {
            return {
                content: [{ type: 'text', text: `Error: No .agent/BOOT.md found at ${agentDir}. Please run 'zeroscan-bootstrap' first.` }],
                isError: true
            };
        }
        return { content: [{ type: 'text', text: fs.readFileSync(bootFile, 'utf8') }] };
    }

    if (name === 'zeroscan_get_map') {
        const mapFile = path.join(agentDir, 'PROJECT_MAP.json');
        if (!fs.existsSync(mapFile)) {
            return { content: [{ type: 'text', text: `Error: No .agent/PROJECT_MAP.json found at ${agentDir}.` }], isError: true };
        }
        const data = JSON.parse(fs.readFileSync(mapFile, 'utf8'));
        if (args.domain && data.domains && data.domains[args.domain]) {
            return { content: [{ type: 'text', text: JSON.stringify(data.domains[args.domain], null, 2) }] };
        }
        return { content: [{ type: 'text', text: JSON.stringify(data, null, 2) }] };
    }

    if (name === 'zeroscan_read_state') {
        const stateFile = path.join(agentDir, 'PROJECT_STATE.json');
        if (!fs.existsSync(stateFile)) {
            return { content: [{ type: 'text', text: `Error: No .agent/PROJECT_STATE.json found at ${agentDir}.` }], isError: true };
        }
        return { content: [{ type: 'text', text: fs.readFileSync(stateFile, 'utf8') }] };
    }

    if (name === 'zeroscan_read_decisions') {
        const decFile = path.join(agentDir, 'DECISIONS.md');
        if (!fs.existsSync(decFile)) {
            return { content: [{ type: 'text', text: `Error: No .agent/DECISIONS.md found at ${agentDir}.` }], isError: true };
        }
        return { content: [{ type: 'text', text: fs.readFileSync(decFile, 'utf8') }] };
    }

    if (name === 'zeroscan_read_next_task') {
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
        const requiredFiles = ['BOOT.md', 'PROJECT_STATE.json', 'PROJECT_MAP.json', 'DECISIONS.md', 'NEXT_TASK.md', 'TASK_LEDGER.jsonl'];
        const bootstrapFiles = ['BOOT.md', 'PROJECT_STATE.json', 'NEXT_TASK.md'];
        const missing = [];
        let bootBytes = 0;
        let totalSystemBytes = 0;

        for (const rf of requiredFiles) {
            const fp = path.join(agentDir, rf);
            if (!fs.existsSync(fp)) {
                missing.push(rf);
            }
        }

        for (const bf of bootstrapFiles) {
            const fp = path.join(agentDir, bf);
            if (fs.existsSync(fp)) {
                bootBytes += fs.statSync(fp).size;
            }
        }

        if (fs.existsSync(agentDir)) {
            const allFiles = fs.readdirSync(agentDir, { recursive: true, withFileTypes: true });
            for (const ent of allFiles) {
                if (ent.isFile()) {
                    try {
                        const entPath = path.join(ent.path || agentDir, ent.name);
                        totalSystemBytes += fs.statSync(entPath).size;
                    } catch {}
                }
            }
        }

        const isValid = missing.length === 0 && bootBytes <= MAX_BOOTSTRAP_CONTEXT_BYTES;
        const pct = ((bootBytes / MAX_BOOTSTRAP_CONTEXT_BYTES) * 100).toFixed(1);
        const statusText = `Zero-Scan Specification Validation:\n- Status: ${isValid ? 'PASS ✅' : 'FAIL ❌'}\n- Bootstrap Context Size: ${bootBytes} / ${MAX_BOOTSTRAP_CONTEXT_BYTES} bytes (${pct}% used, Budget <= 10 KB)\n- Total Agent Memory Size: ${totalSystemBytes} bytes\n- Missing Files: ${missing.length > 0 ? missing.join(', ') : 'None'}\n- Location: ${agentDir}`;
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
        const trimmed = line.trim();
        if (!trimmed) return;

        let reqId = null;
        try {
            const req = JSON.parse(trimmed);
            reqId = req.id;
            const method = req.method;
            const params = req.params || {};

            let response = null;

            if (method === 'initialize') {
                response = { jsonrpc: '2.0', id: reqId, result: handleInitialize(params) };
            } else if (method === 'notifications/initialized') {
                return; // Notifications require no response
            } else if (method === 'tools/list') {
                response = { jsonrpc: '2.0', id: reqId, result: handleToolsList() };
            } else if (method === 'tools/call') {
                response = { jsonrpc: '2.0', id: reqId, result: handleToolsCall(params.name, params.arguments) };
            } else if (method === 'prompts/list') {
                response = { jsonrpc: '2.0', id: reqId, result: handlePromptsList() };
            } else if (method === 'prompts/get') {
                response = { jsonrpc: '2.0', id: reqId, result: handlePromptsGet(params.name, params.arguments) };
            } else if (method === 'ping') {
                response = { jsonrpc: '2.0', id: reqId, result: {} };
            } else {
                response = { jsonrpc: '2.0', id: reqId, error: { code: -32601, message: `Method not found: ${method}` } };
            }

            process.stdout.write(JSON.stringify(response) + '\n');
        } catch (err) {
            const errResp = { jsonrpc: '2.0', id: reqId, error: { code: -32603, message: String(err.message || err) } };
            process.stdout.write(JSON.stringify(errResp) + '\n');
        }
    });
}

if (require.main === module) {
    runStdioServer();
}

module.exports = {
    findAgentDir,
    handleInitialize,
    handleToolsList,
    handlePromptsList,
    handlePromptsGet,
    handleToolsCall,
    runStdioServer
};
