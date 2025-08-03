import OpenAI from 'openai';
import { Anthropic } from '@anthropic-ai/sdk';
import * as vscode from 'vscode';
import { ConfigManager, AgentConfig } from './config';

export interface AnalysisResult {
    summary: string;
    complexity: number;
    suggestions: string[];
    issues: Issue[];
}

export interface Issue {
    severity: 'low' | 'medium' | 'high';
    message: string;
    description: string;
    suggestion?: string;
    line?: number;
}

export interface ReviewResult {
    assessment: string;
    issues: Issue[];
    score: number;
}

export interface ProjectOverview {
    fileCount: number;
    lineCount: number;
    languages: string[];
    summary: string;
    structure: FileStructure[];
}

export interface FileStructure {
    path: string;
    type: 'file' | 'directory';
    language?: string;
    size?: number;
}

export class CodingAgent {
    private openaiClient?: OpenAI;
    private anthropicClient?: Anthropic;
    private config: AgentConfig;
    private configManager: ConfigManager;

    constructor(configManager: ConfigManager) {
        this.configManager = configManager;
        this.config = configManager.getConfig();
        this.initializeClients();

        // Listen for config changes
        configManager.onConfigChange(() => {
            this.config = configManager.getConfig();
            this.initializeClients();
        });
    }

    private initializeClients(): void {
        if (this.config.openaiApiKey) {
            this.openaiClient = new OpenAI({
                apiKey: this.config.openaiApiKey
            });
        }

        if (this.config.anthropicApiKey) {
            this.anthropicClient = new Anthropic({
                apiKey: this.config.anthropicApiKey
            });
        }
    }

    async analyzeCode(code: string, language: string): Promise<AnalysisResult> {
        const prompt = `Analyze the following ${language} code and provide:
1. A brief summary of what the code does
2. A complexity score from 1-10
3. Suggestions for improvement
4. Any potential issues

Code:
\`\`\`${language}
${code}
\`\`\`

Please format your response as JSON with the following structure:
{
  "summary": "Brief description",
  "complexity": number,
  "suggestions": ["suggestion1", "suggestion2"],
  "issues": [{"severity": "low|medium|high", "message": "issue", "description": "detailed description", "line": number}]
}`;

        try {
            const response = await this.callAI(prompt);
            return this.parseAnalysisResponse(response);
        } catch (error) {
            console.error('Code analysis failed:', error);
            throw new Error(`Analysis failed: ${error}`);
        }
    }

    async generateCode(description: string, language: string): Promise<string> {
        const prompt = `Generate ${language} code based on the following description:
${description}

Requirements:
- Write clean, well-documented code
- Follow best practices for ${language}
- Include appropriate comments
- Handle edge cases where relevant

Please provide only the code without any additional explanation.`;

        try {
            const response = await this.callAI(prompt);
            return this.extractCodeFromResponse(response);
        } catch (error) {
            console.error('Code generation failed:', error);
            throw new Error(`Generation failed: ${error}`);
        }
    }

    async reviewCode(code: string, language: string): Promise<ReviewResult> {
        const prompt = `Review the following ${language} code and provide:
1. Overall assessment
2. List of issues with severity levels
3. Overall quality score (1-10)

Code:
\`\`\`${language}
${code}
\`\`\`

Focus on:
- Code quality and readability
- Performance considerations
- Security issues
- Best practices adherence
- Potential bugs

Please format your response as JSON:
{
  "assessment": "Overall assessment",
  "issues": [{"severity": "low|medium|high", "message": "issue", "description": "detailed description", "suggestion": "how to fix"}],
  "score": number
}`;

        try {
            const response = await this.callAI(prompt);
            return this.parseReviewResponse(response);
        } catch (error) {
            console.error('Code review failed:', error);
            throw new Error(`Review failed: ${error}`);
        }
    }

    async fixCode(code: string, language: string): Promise<string> {
        const prompt = `Fix any issues in the following ${language} code while maintaining its functionality:

\`\`\`${language}
${code}
\`\`\`

Please:
- Fix syntax errors
- Improve code quality
- Optimize performance where possible
- Add missing error handling
- Ensure best practices are followed

Provide only the corrected code without additional explanation.`;

        try {
            const response = await this.callAI(prompt);
            return this.extractCodeFromResponse(response);
        } catch (error) {
            console.error('Code fix failed:', error);
            throw new Error(`Fix failed: ${error}`);
        }
    }

    async getProjectOverview(): Promise<ProjectOverview> {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            throw new Error('No workspace folder found');
        }

        try {
            const structure = await this.analyzeProjectStructure(workspaceFolder.uri);
            
            const prompt = `Analyze this project structure and provide an overview:

${JSON.stringify(structure, null, 2)}

Please provide:
1. File and line count estimates
2. Detected programming languages
3. Project summary and purpose
4. Technology stack analysis

Format as JSON:
{
  "fileCount": number,
  "lineCount": number,
  "languages": ["lang1", "lang2"],
  "summary": "Project description"
}`;

            const response = await this.callAI(prompt);
            const overview = this.parseOverviewResponse(response);
            overview.structure = structure;
            
            return overview;
        } catch (error) {
            console.error('Project overview failed:', error);
            throw new Error(`Overview failed: ${error}`);
        }
    }

    async chat(message: string, context?: string): Promise<string> {
        let prompt = message;
        
        if (context) {
            prompt = `Context:\n${context}\n\nUser: ${message}`;
        }

        try {
            return await this.callAI(prompt);
        } catch (error) {
            console.error('Chat failed:', error);
            throw new Error(`Chat failed: ${error}`);
        }
    }

    private async callAI(prompt: string): Promise<string> {
        const isOpenAIModel = this.config.defaultModel.startsWith('gpt');
        
        if (isOpenAIModel && this.openaiClient) {
            return await this.callOpenAI(prompt);
        } else if (!isOpenAIModel && this.anthropicClient) {
            return await this.callAnthropic(prompt);
        } else {
            throw new Error('No valid AI client configured for the selected model');
        }
    }

    private async callOpenAI(prompt: string): Promise<string> {
        if (!this.openaiClient) {
            throw new Error('OpenAI client not initialized');
        }

        const response = await this.openaiClient.chat.completions.create({
            model: this.config.defaultModel,
            messages: [{ role: 'user', content: prompt }],
            max_tokens: this.config.maxTokens,
            temperature: this.config.temperature,
        });

        return response.choices[0]?.message?.content || '';
    }

    private async callAnthropic(prompt: string): Promise<string> {
        if (!this.anthropicClient) {
            throw new Error('Anthropic client not initialized');
        }

        const response = await this.anthropicClient.completions.create({
            model: this.config.defaultModel,
            max_tokens_to_sample: this.config.maxTokens,
            temperature: this.config.temperature,
            prompt: `Human: ${prompt}\n\nAssistant:`,
        });

        return response.completion || '';
    }

    private parseAnalysisResponse(response: string): AnalysisResult {
        try {
            const parsed = JSON.parse(response);
            return {
                summary: parsed.summary || 'Analysis completed',
                complexity: parsed.complexity || 5,
                suggestions: parsed.suggestions || [],
                issues: parsed.issues || []
            };
        } catch {
            return {
                summary: response,
                complexity: 5,
                suggestions: [],
                issues: []
            };
        }
    }

    private parseReviewResponse(response: string): ReviewResult {
        try {
            const parsed = JSON.parse(response);
            return {
                assessment: parsed.assessment || 'Review completed',
                issues: parsed.issues || [],
                score: parsed.score || 7
            };
        } catch {
            return {
                assessment: response,
                issues: [],
                score: 7
            };
        }
    }

    private parseOverviewResponse(response: string): ProjectOverview {
        try {
            const parsed = JSON.parse(response);
            return {
                fileCount: parsed.fileCount || 0,
                lineCount: parsed.lineCount || 0,
                languages: parsed.languages || [],
                summary: parsed.summary || 'Project overview completed',
                structure: []
            };
        } catch {
            return {
                fileCount: 0,
                lineCount: 0,
                languages: [],
                summary: response,
                structure: []
            };
        }
    }

    private extractCodeFromResponse(response: string): string {
        // Extract code from markdown code blocks
        const codeBlockRegex = /```[\w]*\n([\s\S]*?)\n```/g;
        const matches = response.match(codeBlockRegex);
        
        if (matches && matches.length > 0) {
            return matches[0].replace(/```[\w]*\n/, '').replace(/\n```$/, '');
        }
        
        return response;
    }

    private async analyzeProjectStructure(uri: vscode.Uri): Promise<FileStructure[]> {
        const structure: FileStructure[] = [];
        
        try {
            const entries = await vscode.workspace.fs.readDirectory(uri);
            
            for (const [name, type] of entries) {
                if (this.shouldIgnoreFile(name)) {
                    continue;
                }

                const entryUri = vscode.Uri.joinPath(uri, name);
                const entry: FileStructure = {
                    path: name,
                    type: type === vscode.FileType.Directory ? 'directory' : 'file'
                };

                if (type === vscode.FileType.File) {
                    entry.language = this.getLanguageFromExtension(name);
                    try {
                        const stat = await vscode.workspace.fs.stat(entryUri);
                        entry.size = stat.size;
                    } catch {
                        // Ignore stat errors
                    }
                }

                structure.push(entry);
            }
        } catch (error) {
            console.error('Error analyzing project structure:', error);
        }

        return structure;
    }

    private shouldIgnoreFile(filename: string): boolean {
        return this.config.ignorePatterns.some(pattern => {
            if (pattern.includes('*')) {
                const regex = new RegExp(pattern.replace(/\*/g, '.*'));
                return regex.test(filename);
            }
            return filename === pattern;
        });
    }

    private getLanguageFromExtension(filename: string): string {
        const ext = filename.split('.').pop()?.toLowerCase();
        const languageMap: { [key: string]: string } = {
            'ts': 'typescript',
            'js': 'javascript',
            'py': 'python',
            'java': 'java',
            'cpp': 'cpp',
            'c': 'c',
            'cs': 'csharp',
            'go': 'go',
            'rs': 'rust',
            'php': 'php',
            'rb': 'ruby',
            'swift': 'swift',
            'kt': 'kotlin',
            'dart': 'dart',
            'html': 'html',
            'css': 'css',
            'scss': 'scss',
            'json': 'json',
            'xml': 'xml',
            'yaml': 'yaml',
            'yml': 'yaml',
            'md': 'markdown'
        };
        
        return languageMap[ext || ''] || 'text';
    }
}