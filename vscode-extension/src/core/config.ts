import * as vscode from 'vscode';

export interface AgentConfig {
    openaiApiKey: string;
    anthropicApiKey: string;
    defaultModel: string;
    maxTokens: number;
    temperature: number;
    debug: boolean;
    ignorePatterns: string[];
    autoSave: boolean;
    showInlineComments: boolean;
}

export class ConfigManager {
    private config: vscode.WorkspaceConfiguration;

    constructor() {
        this.config = vscode.workspace.getConfiguration('aiCodingAgent');
    }

    getConfig(): AgentConfig {
        return {
            openaiApiKey: this.config.get('openaiApiKey', ''),
            anthropicApiKey: this.config.get('anthropicApiKey', ''),
            defaultModel: this.config.get('defaultModel', 'gpt-4'),
            maxTokens: this.config.get('maxTokens', 4000),
            temperature: this.config.get('temperature', 0.1),
            debug: this.config.get('debug', false),
            ignorePatterns: this.config.get('ignorePatterns', [
                '__pycache__', '*.pyc', '.git', 'node_modules', '*.min.js', 'dist', 'build'
            ]),
            autoSave: this.config.get('autoSave', true),
            showInlineComments: this.config.get('showInlineComments', true)
        };
    }

    async updateConfig(key: string, value: any): Promise<void> {
        await this.config.update(key, value, vscode.ConfigurationTarget.Global);
        this.config = vscode.workspace.getConfiguration('aiCodingAgent');
    }

    onConfigChange(callback: () => void): vscode.Disposable {
        return vscode.workspace.onDidChangeConfiguration(event => {
            if (event.affectsConfiguration('aiCodingAgent')) {
                this.config = vscode.workspace.getConfiguration('aiCodingAgent');
                callback();
            }
        });
    }

    validateConfig(): { isValid: boolean; errors: string[] } {
        const config = this.getConfig();
        const errors: string[] = [];

        if (!config.openaiApiKey && !config.anthropicApiKey) {
            errors.push('At least one API key (OpenAI or Anthropic) must be configured');
        }

        if (config.maxTokens <= 0) {
            errors.push('Max tokens must be greater than 0');
        }

        if (config.temperature < 0 || config.temperature > 1) {
            errors.push('Temperature must be between 0 and 1');
        }

        return {
            isValid: errors.length === 0,
            errors
        };
    }
}