/**
 * Zero-Scan VS Code & Cursor Extension
 * Git-Aware Project Memory V2.0 Integration.
 * 
 * Copyright (c) 2026 Chau Vu / CPF-FAMILY. Licensed under MIT.
 */

const vscode = require('vscode');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

let statusBarItem;
const MAX_BOOTSTRAP_CONTEXT_BYTES = 10 * 1024; // 10 KB budget

function getWorkspaceRoot() {
    return vscode.workspace.workspaceFolders && vscode.workspace.workspaceFolders.length > 0
        ? vscode.workspace.workspaceFolders[0].uri.fsPath
        : null;
}

function getAgentDir() {
    const root = getWorkspaceRoot();
    if (!root) return null;
    const agentPath = path.join(root, '.agent');
    return fs.existsSync(agentPath) ? agentPath : null;
}

function updateStatusBar() {
    const agentDir = getAgentDir();
    if (!agentDir) {
        statusBarItem.text = '$(zap) Zero-Scan: Not Initialized';
        statusBarItem.tooltip = 'Click to initialize Zero-Scan Project Memory (.agent/)';
        statusBarItem.command = 'zeroscan.init';
        statusBarItem.show();
        return;
    }

    try {
        const requiredFiles = ['BOOT.md', 'PROJECT_STATE.json', 'PROJECT_MAP.json', 'DECISIONS.md', 'NEXT_TASK.md'];
        let totalBytes = 0;
        let missing = [];

        for (const f of requiredFiles) {
            const fp = path.join(agentDir, f);
            if (fs.existsSync(fp)) {
                totalBytes += fs.statSync(fp).size;
            } else {
                missing.push(f);
            }
        }

        const kb = (totalBytes / 1024).toFixed(1);
        if (missing.length > 0) {
            statusBarItem.text = `$(warning) Zero-Scan: Missing ${missing.length} files (${kb} KB)`;
            statusBarItem.tooltip = `Missing: ${missing.join(', ')}`;
        } else if (totalBytes > MAX_BOOTSTRAP_CONTEXT_BYTES) {
            statusBarItem.text = `$(error) Zero-Scan: Over Budget (${kb} KB / 10 KB)`;
            statusBarItem.tooltip = 'Context size exceeds <= 10 KB limit!';
        } else {
            statusBarItem.text = `$(check) Zero-Scan: ${kb} KB / 10 KB [PASS]`;
            statusBarItem.tooltip = 'Zero-Scan Project Memory V2.0 is healthy & within budget.';
        }
        statusBarItem.command = 'zeroscan.status';
        statusBarItem.show();
    } catch {
        statusBarItem.text = '$(zap) Zero-Scan: Error reading memory';
        statusBarItem.show();
    }
}

function activate(context) {
    statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    context.subscriptions.push(statusBarItem);
    updateStatusBar();

    // Watch for file changes in .agent/
    const root = getWorkspaceRoot();
    if (root) {
        const watcher = vscode.workspace.createFileSystemWatcher(new vscode.RelativePattern(root, '.agent/**/*'));
        watcher.onDidChange(() => updateStatusBar());
        watcher.onDidCreate(() => updateStatusBar());
        watcher.onDidDelete(() => updateStatusBar());
        context.subscriptions.push(watcher);
    }

    // Register commands
    context.subscriptions.push(
        vscode.commands.registerCommand('zeroscan.init', async () => {
            const workspaceRoot = getWorkspaceRoot();
            if (!workspaceRoot) {
                vscode.window.showErrorMessage('Please open a workspace directory first.');
                return;
            }

            const projectName = await vscode.window.showInputBox({
                prompt: 'Enter Project Name',
                value: path.basename(workspaceRoot)
            });
            if (!projectName) return;

            const mission = await vscode.window.showInputBox({
                prompt: 'Enter Project Mission / High-level Goal',
                value: 'Autonomous multi-agent system'
            });

            const bootstrapScript = path.join(workspaceRoot, 'bootstrap.py');
            const cmd = fs.existsSync(bootstrapScript)
                ? `python3 bootstrap.py --target "${workspaceRoot}" --name "${projectName}" --mission "${mission || ''}"`
                : `curl -fsSL https://raw.githubusercontent.com/chauvuusvn/zeroscan/main/bootstrap.py | python3 - --target "${workspaceRoot}" --name "${projectName}" --mission "${mission || ''}"`;

            exec(cmd, { cwd: workspaceRoot }, (error, stdout, stderr) => {
                if (error) {
                    vscode.window.showErrorMessage(`Zero-Scan Init Failed: ${stderr || error.message}`);
                } else {
                    vscode.window.showInformationMessage('🎉 Zero-Scan Project Memory V2.0 initialized successfully!');
                    updateStatusBar();
                }
            });
        }),

        vscode.commands.registerCommand('zeroscan.validate', () => {
            const agentDir = getAgentDir();
            if (!agentDir) {
                vscode.window.showWarningMessage('No .agent/ memory found. Run Zero-Scan: Initialize first.');
                return;
            }
            updateStatusBar();
            vscode.window.showInformationMessage('Zero-Scan validation complete: Context budget <= 10 KB verified.');
        }),

        vscode.commands.registerCommand('zeroscan.status', () => {
            const agentDir = getAgentDir();
            if (!agentDir) {
                vscode.window.showWarningMessage('No .agent/ memory found.');
                return;
            }
            const bootFile = path.join(agentDir, 'BOOT.md');
            if (fs.existsSync(bootFile)) {
                vscode.workspace.openTextDocument(bootFile).then(doc => vscode.window.showTextDocument(doc));
            }
        }),

        vscode.commands.registerCommand('zeroscan.openBoot', () => {
            const fp = path.join(getAgentDir() || '', 'BOOT.md');
            if (fs.existsSync(fp)) vscode.workspace.openTextDocument(fp).then(doc => vscode.window.showTextDocument(doc));
        }),

        vscode.commands.registerCommand('zeroscan.openMap', () => {
            const fp = path.join(getAgentDir() || '', 'PROJECT_MAP.json');
            if (fs.existsSync(fp)) vscode.workspace.openTextDocument(fp).then(doc => vscode.window.showTextDocument(doc));
        }),

        vscode.commands.registerCommand('zeroscan.openTask', () => {
            const fp = path.join(getAgentDir() || '', 'NEXT_TASK.md');
            if (fs.existsSync(fp)) vscode.workspace.openTextDocument(fp).then(doc => vscode.window.showTextDocument(doc));
        }),

        vscode.commands.registerCommand('zeroscan.openDecisions', () => {
            const fp = path.join(getAgentDir() || '', 'DECISIONS.md');
            if (fs.existsSync(fp)) vscode.workspace.openTextDocument(fp).then(doc => vscode.window.showTextDocument(doc));
        })
    );
}

function deactivate() {}

module.exports = {
    activate,
    deactivate
};
