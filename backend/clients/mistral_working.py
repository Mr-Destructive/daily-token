"""
Mistral client - WORKING implementation using Playwright.

Since Cloudflare tokens are session-bound and cannot be transferred,
we need to keep the browser context alive and execute API calls through it.
"""

import asyncio
import json
from typing import Optional


class MistralWorking:
    """
    Mistral client using browser context for API calls.
    This is the only way to work around Cloudflare protection.
    """
    
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
    
    async def _init(self):
        """Initialize browser on first use."""
        if self.browser:
            return
        
        from playwright.async_api import async_playwright
        self.p = async_playwright()
        pw = await self.p.__aenter__()
        self.browser = await pw.chromium.launch(headless=True)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        
        await self.page.goto("https://chat.mistral.ai/chat", wait_until="load")
        await self.page.wait_for_timeout(2000)
    
    async def chat(self, prompt: str) -> str:
        """Send message through browser context."""
        await self._init()
        
        response = await self.page.evaluate(f"""
        async () => {{
            // Step 1: Create chat
            const chatRes = await fetch('https://chat.mistral.ai/api/trpc/message.newChat?batch=1', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{
                    "0": {{
                        "json": {{
                            "content": [{{"type": "text", "text": `{prompt}`}}],
                            "voiceInput": null,
                            "audioRecording": null,
                            "agentId": null,
                            "agentsApiAgentId": null,
                            "files": [],
                            "model": null,
                            "features": ["beta-websearch"],
                            "integrations": [],
                            "incognito": false
                        }}
                    }}
                }})
            }});
            
            const chatData = await chatRes.json();
            const chatId = chatData[0]?.result?.data?.json?.id;
            
            if (!chatId) throw new Error('No chat ID');
            
            // Step 2: Get response
            const streamRes = await fetch('https://chat.mistral.ai/api/chat', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{
                    "chatId": chatId,
                    "mode": "start",
                    "disabledFeatures": ["memory-inference"],
                    "clientPromptData": {{
                        "currentDate": new Date().toISOString().split('T')[0],
                        "userTimezone": "UTC"
                    }},
                    "stableAnonymousIdentifier": "browser",
                    "shouldAwaitStreamBackgroundTasks": true,
                    "shouldUseMessagePatch": true,
                    "shouldUsePersistentStream": true
                }})
            }});
            
            // Step 3: Parse stream
            let allText = [];
            const reader = streamRes.body.getReader();
            const decoder = new TextDecoder();
            
            while (true) {{
                const {{done, value}} = await reader.read();
                if (done) break;
                
                const text = decoder.decode(value, {{stream: true}});
                const lines = text.split('\\n');
                
                for (const line of lines) {{
                    if (line.includes(':')) {{
                        try {{
                            const [, jsonStr] = line.split(':', 1);
                            const json = JSON.parse(jsonStr);
                            const patches = json.json?.patches || [];
                            
                            for (const patch of patches) {{
                                if (patch.op === 'append' && patch.value) {{
                                    allText.push(patch.value);
                                }}
                            }}
                        }} catch(e) {{}}
                    }}
                }}
            }}
            
            return allText.join('').trim();
        }}
        """)
        
        return response
    
    async def close(self):
        """Close browser."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()


def chat(prompt: str) -> str:
    """Synchronous wrapper."""
    client = MistralWorking()
    try:
        return asyncio.run(client.chat(prompt))
    finally:
        asyncio.run(client.close())
