import * as vscode from 'vscode';

export interface HistoryItem {
    id: string;
    title: string;
    timestamp: Date;
    type: 'chat' | 'analysis' | 'generation' | 'review' | 'fix';
    summary?: string;
}

export class HistoryProvider implements vscode.TreeDataProvider<HistoryItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<HistoryItem | undefined | null | void> = new vscode.EventEmitter<HistoryItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<HistoryItem | undefined | null | void> = this._onDidChangeTreeData.event;

    private history: HistoryItem[] = [];

    constructor() {}

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: HistoryItem): vscode.TreeItem {
        const item = new vscode.TreeItem(element.title, vscode.TreeItemCollapsibleState.None);
        
        item.tooltip = `${element.type.toUpperCase()} - ${element.timestamp.toLocaleString()}`;
        item.description = element.summary;
        item.contextValue = 'historyItem';
        
        // Set different icons based on type
        switch (element.type) {
            case 'chat':
                item.iconPath = new vscode.ThemeIcon('comment');
                break;
            case 'analysis':
                item.iconPath = new vscode.ThemeIcon('search');
                break;
            case 'generation':
                item.iconPath = new vscode.ThemeIcon('add');
                break;
            case 'review':
                item.iconPath = new vscode.ThemeIcon('checklist');
                break;
            case 'fix':
                item.iconPath = new vscode.ThemeIcon('wrench');
                break;
            default:
                item.iconPath = new vscode.ThemeIcon('file');
        }

        return item;
    }

    getChildren(element?: HistoryItem): Thenable<HistoryItem[]> {
        if (!element) {
            // Return sorted history (newest first)
            return Promise.resolve(this.history.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime()));
        }
        return Promise.resolve([]);
    }

    addHistoryItem(item: Omit<HistoryItem, 'id' | 'timestamp'>): void {
        const historyItem: HistoryItem = {
            ...item,
            id: this.generateId(),
            timestamp: new Date()
        };

        this.history.push(historyItem);
        
        // Keep only the last 50 items
        if (this.history.length > 50) {
            this.history = this.history.slice(-50);
        }

        this.refresh();
    }

    clearHistory(): void {
        this.history = [];
        this.refresh();
    }

    getHistoryItem(id: string): HistoryItem | undefined {
        return this.history.find(item => item.id === id);
    }

    private generateId(): string {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }
}