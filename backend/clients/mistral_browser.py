"""
Mistral AI client - Browser-based implementation.

This version uses Playwright to make API calls through a real browser context,
which ensures Cloudflare tokens are valid.
"""

import asyncio
import json
from typing import Optional


class MistralBrowser:
    """Mistral client using Playwright browser context."""
    
    def __init__(self):
        self.base_url = "https://chat.mistral.ai"
        self.browser = None
        self.context = None
        self.page = None
        
    async def _init_browser(self):
        """Initialize browser context."""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise ImportError("Playwright required: pip install playwright")
        
        if not self.browser:
            self.playwright = async_playwright()
            p = await self.playwright.__aenter__()
            self.browser = await p.chromium.launch(headless=True)
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()
            
            # Navigate to establish session
            await self.page.goto(f"{self.base_url}/chat", wait_until="load", timeout=15000)
            await self.page.wait_for_timeout(2000)
    
    async def close(self):
        """Close browser."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
    
    async def chat(self, prompt: str) -> str:
        """Send prompt to Mistral via browser context."""
        await self._init_browser()
        
        try:
            # Make API call through browser (ensures valid Cloudflare tokens)
            response = await self.page.evaluate("""
            async (prompt) => {
                // Step 1: Create new chat
                const chatResponse = await fetch(
                    'https://chat.mistral.ai/api/trpc/message.newChat?batch=1',
                    {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            "0": {
                                "json": {
                                    "content": [{"type": "text", "text": prompt}],
                                    "voiceInput": null,
                                    "audioRecording": null,
                                    "agentId": null,
                                    "agentsApiAgentId": null,
                                    "files": [],
                                    "model": null,
                                    "features": ["beta-websearch"],
                                    "integrations": [],
                                    "incognito": false,
                                }
                            }
                        })
                    }
                );
                
                const chatData = await chatResponse.json();
                const chatId = chatData[0]?.result?.data?.json?.id;
                
                if (!chatId) {
                    throw new Error('No chat ID in response');
                }
                
                // Step 2: Get response
                const streamResponse = await fetch(
                    'https://chat.mistral.ai/api/chat',
                    {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            "chatId": chatId,
                            "mode": "start",
                            "disabledFeatures": ["memory-inference"],
                            "clientPromptData": {
                                "currentDate": new Date().toISOString().split('T')[0],
                                "userTimezone": "UTC"
                            },
                            "stableAnonymousIdentifier": "browser-session",
                            "shouldAwaitStreamBackgroundTasks": true,
                            "shouldUseMessagePatch": true,
                            "shouldUsePersistentStream": true
                        })
                    }
                );
                
                // Step 3: Parse streaming response
                const reader = streamResponse.body.getReader();
                const decoder = new TextDecoder();
                let allText = [];
                
                while (true) {
                    const {done, value} = await reader.read();
                    if (done) break;
                    
                    const text = decoder.decode(value, {stream: true});
                    const lines = text.split('\\n');
                    
                    for (const line of lines) {
                        if (line.includes(':')) {
                            try {
                                const json = JSON.parse(line.split(':', 1)[1]);
                                const patches = json.json?.patches || [];
                                
                                for (const patch of patches) {
                                    if (patch.op === 'append') {
                                        const value = patch.value;
                                        if (value) {
                                            allText.push(value);
                                        }
                                    }
                                }
                            } catch (e) {
                                // Skip parsing errors
                            }
                        }
                    }
                }
                
                return allText.join('').trim();
            }
            """, prompt)
            
            return response
        
        except Exception as e:
            raise Exception(f"Browser chat failed: {e}")


# Synchronous wrapper for easier use
class Mistral:
    """Synchronous Mistral client using browser."""
    
    def __init__(self):
        self.browser_client = MistralBrowser()
    
    def chat(self, prompt: str) -> str:
        """Send prompt to Mistral."""
        try:
            return asyncio.run(self.browser_client.chat(prompt))
        except Exception as e:
            raise Exception(f"Mistral: {e}")
    
    def close(self):
        """Close browser."""
        asyncio.run(self.browser_client.close())
    
    def __del__(self):
        """Cleanup on deletion."""
        try:
            self.close()
        except:
            pass
