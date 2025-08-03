import * as vscode from 'vscode';
import { CodingAgent } from '../core/agent';

export interface ToolItem {
    label: string;
    command: string;
    description: string;
    icon: string;
    category: string;
}

export class ToolsProvider implements vscode.TreeDataProvider<ToolItem | string> {
    private _onDidChangeTreeData: vscode.EventEmitter<ToolItem | string | undefined | null | void> = new vscode.EventEmitter<ToolItem | string | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<ToolItem | string | undefined | null | void> = this._onDidChangeTreeData.event;

    private tools: { [category: string]: ToolItem[] } = {
        'Analysis': [
            {
                label: 'Analyze Current File',
                command: 'aiCodingAgent.analyzeFile',
                description: 'Analyze the currently open file',
                icon: 'search',
                category: 'Analysis'
            },
            {
                label: 'Project Overview',
                command: 'aiCodingAgent.projectOverview',
                description: 'Get an overview of your project',
                icon: 'file-directory',
                category: 'Analysis'
            }
        ],
        'Code Generation': [
            {
                label: 'Generate Code',
                command: 'aiCodingAgent.generateCode',
                description: 'Generate code from description',
                icon: 'add',
                category: 'Code Generation'
            }
        ],
        'Code Quality': [
            {
                label: 'Review Code',
                command: 'aiCodingAgent.reviewCode',
                description: 'Review code for quality and issues',
                icon: 'checklist',
                category: 'Code Quality'
            },
            {
                label: 'Fix Code Issues',
                command: 'aiCodingAgent.fixCode',
                description: 'Automatically fix code issues',
                icon: 'wrench',
                category: 'Code Quality'
            }
        ],
        'Settings': [
            {
                label: 'Open Settings',
                command: 'aiCodingAgent.openSettings',
                description: 'Configure AI Coding Agent',
                icon: 'settings',
                category: 'Settings'
            }
        ]
    };

    constructor(private agent: CodingAgent) {}

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: ToolItem | string): vscode.TreeItem {
        if (typeof element === 'string') {
            // Category item
            const item = new vscode.TreeItem(element, vscode.TreeItemCollapsibleState.Expanded);
            item.contextValue = 'category';
            item.iconPath = new vscode.ThemeIcon('folder');
            return item;
        } else {
            // Tool item
            const item = new vscode.TreeItem(element.label, vscode.TreeItemCollapsibleState.None);
            item.description = element.description;
            item.command = {
                command: element.command,
                title: element.label
            };
            item.iconPath = new vscode.ThemeIcon(element.icon);
            item.contextValue = 'tool';
            return item;
        }
    }

    getChildren(element?: ToolItem | string): Thenable<(ToolItem | string)[]> {
        if (!element) {
            // Return categories
            return Promise.resolve(Object.keys(this.tools));
        } else if (typeof element === 'string') {
            // Return tools in category
            return Promise.resolve(this.tools[element] || []);
        }
        return Promise.resolve([]);
    }

    getParent(element: ToolItem | string): vscode.ProviderResult<ToolItem | string> {
        if (typeof element === 'string') {
            return undefined; // Categories have no parent
        } else {
            return element.category;
        }
    }
}