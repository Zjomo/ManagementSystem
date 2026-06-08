import { cleanText } from "@/lib/utils";
import { buildMermaidSystemPrompt } from "@/lib/prompts/mermaid";

export async function POST(request) {
  try {
    const { text, diagramType, aiConfig, accessPassword, selectedModel } = await request.json();

    if (!text) {
      return Response.json({ error: "请提供文本内容" }, { status: 400 });
    }

    const cleanedText = cleanText(text);
    
    let finalConfig;
    
    // 步骤1: 检查是否有完整的aiConfig
    const hasCompleteAiConfig = aiConfig?.apiUrl && aiConfig?.apiKey && aiConfig?.modelName;
    
    if (hasCompleteAiConfig) {
      // 如果有完整的aiConfig，直接使用
      finalConfig = {
        apiUrl: aiConfig.apiUrl,
        apiKey: aiConfig.apiKey,
        modelName: aiConfig.modelName
      };
    } else {
      // 步骤2: 如果没有完整的aiConfig，则检验accessPassword
      if (accessPassword) {
        // 步骤3: 如果传入了accessPassword，验证是否有效
        const correctPassword = process.env.ACCESS_PASSWORD;
        const isPasswordValid = correctPassword && accessPassword === correctPassword;
        
        if (!isPasswordValid) {
          // 如果密码无效，直接报错
          return Response.json({ 
            error: "访问密码无效" 
          }, { status: 401 });
        }
      }
      
      // 如果没有传入accessPassword或者accessPassword有效，使用环境变量配置
      // 如果有选择的模型，使用选择的模型，否则使用默认模型
      finalConfig = {
        apiUrl: process.env.AI_API_URL,
        apiKey: process.env.AI_API_KEY,
        modelName: process.env.AI_MODEL_NAME || selectedModel
      };
    }

    // 检查最终配置是否完整
    if (!finalConfig.apiUrl || !finalConfig.apiKey || !finalConfig.modelName) {
      return Response.json({ 
        error: "AI配置不完整，请在设置中配置API URL、API Key和模型名称" 
      }, { status: 400 });
    }

    // 构建规范化的 system prompt（中文，按图类型约束）
    const systemPrompt = buildMermaidSystemPrompt({ diagramType: diagramType || "auto", language: "zh" });

    const messages = [
      {
        role: "system",
        content: systemPrompt,
      },
      {
        role: "user",
        content: cleanedText,
      },
    ];

    // 构建API URL
    const url = finalConfig.apiUrl.includes("v1") || finalConfig.apiUrl.includes("v3") 
      ? `${finalConfig.apiUrl}/chat/completions` 
      : `${finalConfig.apiUrl}/v1/chat/completions`;
    
    console.log('Using AI config:', { 
      url, 
      modelName: finalConfig.modelName,
      hasApiKey: !!finalConfig.apiKey,
    });

    // 创建一个 SSE 流式响应
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      async start(controller) {
        const sendEvent = (obj) => {
          controller.enqueue(encoder.encode(`data: ${JSON.stringify(obj)}\n\n`));
        };
        try {
          // 发送请求到 AI API (开启流式模式)
          const response = await fetch(url, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "Authorization": `Bearer ${finalConfig.apiKey}`,
            },
            body: JSON.stringify({
              model: finalConfig.modelName,
              messages,
              stream: true,
            }),
          });

          if (!response.ok) {
            const errorText = await response.text();
            console.error("AI API Error:", response.status, errorText);
            sendEvent({ type: "error", message: `AI服务返回错误 (${response.status})`, ok: false });
            controller.close();
            return;
          }

          // 读取上游流式响应并增量提取 mermaid fenced code
          const reader = response.body.getReader();
          const decoder = new TextDecoder();
          let pending = ""; // 待处理缓冲
          let mode = "search"; // search | collect | done
          let finalCollected = ""; // 最终代码
          let rawAll = ""; // 兜底：若未找到 fenced，则返回原始文本

          const processIncoming = (text) => {
            const out = [];
            pending += text;
            while (true) {
              if (mode === "search") {
                const idxMer = pending.indexOf("```mermaid");
                const idxFence = pending.indexOf("```");
                let idx = -1;
                if (idxMer !== -1 && (idxFence === -1 || idxMer <= idxFence)) {
                  idx = idxMer;
                } else if (idxFence !== -1) {
                  idx = idxFence;
                }
                if (idx === -1) {
                  break; // 等待更多数据
                }
                const nlIdx = pending.indexOf("\n", idx);
                if (nlIdx === -1) {
                  break; // fence 行未完整
                }
                // 丢弃 fence 行及之前内容
                pending = pending.substring(nlIdx + 1);
                mode = "collect";
              } else if (mode === "collect") {
                const closeIdx = pending.indexOf("```");
                if (closeIdx === -1) {
                  if (pending.length > 0) {
                    out.push(pending);
                    pending = "";
                  }
                  break;
                }
                out.push(pending.substring(0, closeIdx));
                pending = pending.substring(closeIdx + 3);
                mode = "done";
              } else {
                break;
              }
            }
            return out;
          };

          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value, { stream: true });

            // OpenAI 风格 SSE：逐行解析 data: 行
            const lines = chunk.split('\n').filter(line => line.trim() !== '');
            for (const line of lines) {
              if (line.startsWith('data: ')) {
                const data = line.substring(6);
                if (data === '[DONE]') continue;
                try {
                  const parsed = JSON.parse(data);
                  const content = parsed.choices[0]?.delta?.content || '';
                  if (content) {
                    rawAll += content;
                    const increments = processIncoming(content);
                    if (increments.length > 0) {
                      for (const inc of increments) {
                        finalCollected += inc;
                        sendEvent({ type: 'chunk', data: inc });
                      }
                    }
                  }
                } catch (e) {
                  console.error('Error parsing upstream chunk:', e);
                }
              }
            }
          }

          const finalCode = finalCollected.trim() || rawAll.trim();
          sendEvent({ type: 'final', data: finalCode, ok: true });
        } catch (error) {
          console.error("Streaming Error:", error);
          const safeMsg = error?.message || '未知错误';
          controller.enqueue(encoder.encode(`data: ${JSON.stringify({ type: 'error', message: `处理请求时发生错误: ${safeMsg}`, ok: false })}\n\n`));
        } finally {
          controller.close();
        }
      }
    });

    // 返回 SSE 流式响应
    return new Response(stream, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'X-Accel-Buffering': 'no',
      },
    });
  } catch (error) {
    console.error("API Route Error:", error);
    return Response.json(
      { error: `处理请求时发生错误: ${error.message}` }, 
      { status: 500 }
    );
  }
} 