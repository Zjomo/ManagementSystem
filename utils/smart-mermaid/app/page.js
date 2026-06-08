"use client";

import { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Wand2, PanelLeftClose, PanelLeftOpen, RotateCcw } from "lucide-react";
import { Header } from "@/components/header";
import { SettingsDialog } from "@/components/settings-dialog";
import { TextInput } from "@/components/text-input";
import { FileUpload } from "@/components/file-upload";
import { DiagramTypeSelector } from "@/components/diagram-type-selector";
import { ModelSelector } from "@/components/model-selector";
import { MermaidEditor } from "@/components/mermaid-editor";
import { MermaidRenderer } from "@/components/mermaid-renderer";
// import { ExcalidrawRenderer } from "@/components/excalidraw-renderer";
import { generateMermaidFromText } from "@/lib/ai-service";
import { isWithinCharLimit } from "@/lib/utils";
import { isPasswordVerified, hasCustomAIConfig, hasUnlimitedAccess } from "@/lib/config-service";
// Removed auto-fix and direction toggle features
import { Switch } from "@/components/ui/switch";
import { HistoryList } from "@/components/history-list";
import { getHistory, addHistoryEntry, deleteHistoryEntry, clearHistory } from "@/lib/history-service";
// Replaced renderer select with a Switch
import { 
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter
} from "@/components/ui/dialog";
import dynamic from "next/dynamic";

const ExcalidrawRenderer = dynamic(() => import("@/components/excalidraw-renderer"), { ssr: false });

const usageLimit = parseInt(process.env.NEXT_PUBLIC_DAILY_USAGE_LIMIT || "5");

// Usage tracking functions
const checkUsageLimit = () => {
  const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD format
  const usageData = JSON.parse(localStorage.getItem('usageData') || '{}');
  const todayUsage = usageData[today] || 0;
  return todayUsage < usageLimit; // Return true if within limit
};

const incrementUsage = () => {
  const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD format
  const usageData = JSON.parse(localStorage.getItem('usageData') || '{}');
  
  if (!usageData[today]) {
    usageData[today] = 0;
  }
  
  usageData[today] += 1;
  localStorage.setItem('usageData', JSON.stringify(usageData));
};

const checkAndIncrementUsage = () => {
  const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD format
  const usageData = JSON.parse(localStorage.getItem('usageData') || '{}');
  
  if (!usageData[today]) {
    usageData[today] = 0;
  }
  
  if (usageData[today] >= usageLimit) {
    return false; // Limit exceeded
  }
  
  usageData[today] += 1;
  localStorage.setItem('usageData', JSON.stringify(usageData));
  return true; // Within limit
};

const getRemainingUsage = () => {
  const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD format
  const usageData = JSON.parse(localStorage.getItem('usageData') || '{}');
  const todayUsage = usageData[today] || 0;
  return Math.max(0, usageLimit - todayUsage);
};



export default function Home() {
  const [inputText, setInputText] = useState("");
  const [mermaidCode, setMermaidCode] = useState("");
  const [diagramType, setDiagramType] = useState("auto");
  const [isGenerating, setIsGenerating] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [remainingUsage, setRemainingUsage] = useState(5);
  const [showLimitDialog, setShowLimitDialog] = useState(false);
  const [showSettingsDialog, setShowSettingsDialog] = useState(false);
  const [showContactDialog, setShowContactDialog] = useState(false);
  const [passwordVerified, setPasswordVerified] = useState(false);
  const [hasCustomConfig, setHasCustomConfig] = useState(false);
  
  // 新增状态：左侧面板折叠和渲染模式
  const [isLeftPanelCollapsed, setIsLeftPanelCollapsed] = useState(false);
  const [renderMode, setRenderMode] = useState("excalidraw"); // "excalidraw" | "mermaid"
  // Removed fixing state as smart-fix button is removed
  const [showRealtime, setShowRealtime] = useState(false);
  const [leftTab, setLeftTab] = useState("manual");
  const [historyEntries, setHistoryEntries] = useState([]);

  // 错误状态管理
  const [errorMessage, setErrorMessage] = useState(null);
  const [hasError, setHasError] = useState(false);
  
  const maxChars = parseInt(process.env.NEXT_PUBLIC_MAX_CHARS || "20000");

  useEffect(() => {
    // Update remaining usage count on component mount
    setRemainingUsage(getRemainingUsage());
    // Check password verification status
    setPasswordVerified(isPasswordVerified());
    // Check custom AI config status
    setHasCustomConfig(hasCustomAIConfig());
    // Load history list
    setHistoryEntries(getHistory());
  }, []);

  const handleTextChange = (text) => {
    setInputText(text);
  };

  const handleFileTextExtracted = (text) => {
    setInputText(text);
  };

  const handleDiagramTypeChange = (type) => {
    setDiagramType(type);
  };

  const handleMermaidCodeChange = (code) => {
    setMermaidCode(code);
  };

  const handleStreamChunk = (chunk) => {
    setStreamingContent(prev => prev + chunk);
  };

  const handleSettingsClick = () => {
    setShowSettingsDialog(true);
  };

  const handleContactClick = () => {
    setShowContactDialog(true);
  };

  const handlePasswordVerified = (verified) => {
    setPasswordVerified(verified);
  };

  const handleConfigUpdated = () => {
    // 重新检查自定义配置状态
    setHasCustomConfig(hasCustomAIConfig());
  };

  // 渲染模式切换为 Excalidraw 时，模拟“重置视图”按钮点击
  useEffect(() => {
    if (renderMode === "excalidraw") {
      const t = setTimeout(() => {
        try {
          window.dispatchEvent(new CustomEvent('resetView'));
        } catch {}
      }, 0);
      return () => clearTimeout(t);
    }
  }, [renderMode]);

  // 处理错误状态变化
  const handleErrorChange = (error, hasErr) => {
    setErrorMessage(error);
    setHasError(hasErr);
  };

  // 切换左侧面板
  const toggleLeftPanel = () => {
    setIsLeftPanelCollapsed(!isLeftPanelCollapsed);
  };

  // 渲染模式通过下拉选择器切换

  // 使用useCallback优化ModelSelector的回调
  const handleModelChange = useCallback((modelId) => {
    console.log('Selected model:', modelId);
  }, []);

  // Removed smart-fix and direction toggle handlers

  const handleGenerateClick = async () => {
    if (!inputText.trim()) {
      toast.error("请输入文本内容");
      return;
    }

    if (!isWithinCharLimit(inputText, maxChars)) {
      toast.error(`文本超过${maxChars}字符限制`);
      return;
    }

    // 检查是否有无限量权限（密码验证通过或有自定义AI配置）
    const hasUnlimited = hasUnlimitedAccess();
    
    // 如果没有无限量权限，则检查使用限制（但不增加使用量）
    if (!hasUnlimited) {
      if (!checkUsageLimit()) {
        setShowLimitDialog(true);
        return;
      }
    }

    setIsGenerating(true);
    setIsStreaming(showRealtime);
    setStreamingContent("");

    try {
      const { mermaidCode: generatedCode, error } = await generateMermaidFromText(
        inputText,
        diagramType,
        showRealtime ? handleStreamChunk : null
      );

      if (error) {
        toast.error(error);
        return;
      }

      if (!generatedCode) {
        toast.error("生成图表失败，请重试");
        return;
      }

      // 只有在API调用成功后才增加使用量
      if (!hasUnlimited) {
        incrementUsage();
        setRemainingUsage(getRemainingUsage());
      }

      setMermaidCode(generatedCode);
      // 保存到历史记录
      try {
        addHistoryEntry({ inputText, mermaidCode: generatedCode, diagramType });
        setHistoryEntries(getHistory());
      } catch {}
      toast.success("图表生成成功");
    } catch (error) {
      console.error("Generation error:", error);
      toast.error("生成图表时发生错误");
    } finally {
      setIsGenerating(false);
      setIsStreaming(false);
    }
  };

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <Header 
        remainingUsage={remainingUsage}
        usageLimit={usageLimit}
        onSettingsClick={handleSettingsClick}
        onContactClick={handleContactClick}
        isPasswordVerified={passwordVerified}
        hasCustomConfig={hasCustomConfig}
      />
      
      <main className="flex-1 overflow-hidden">
        <div className="h-full p-4 md:p-6">
          <div 
            className={`h-full grid gap-4 md:gap-6 transition-all duration-300 ${
              isLeftPanelCollapsed ? 'grid-cols-1' : 'grid-cols-1 md:grid-cols-3'
            }`}
          >
            {/* 左侧面板 */}
            <div className={`${
              isLeftPanelCollapsed ? 'hidden md:hidden' : 'col-span-1'
            } flex flex-col h-full overflow-hidden`}>
              
              <Tabs value={leftTab} onValueChange={setLeftTab} className="flex flex-col h-full">
                {/* 固定高度的顶部控制栏 */}
                <div className="h-auto md:h-12 flex flex-col md:flex-row justify-between items-start md:items-center gap-2 flex-shrink-0 pb-2 md:pb-0">
                  <TabsList className="h-9 w-full md:w-auto">
                    <TabsTrigger value="manual" className="flex-1 md:flex-none">手动输入</TabsTrigger>
                    <TabsTrigger value="file" className="flex-1 md:flex-none">文件上传</TabsTrigger>
                    <TabsTrigger value="history" className="flex-1 md:flex-none">历史记录</TabsTrigger>
                  </TabsList>
                  <div className="flex items-center gap-2 w-full md:w-auto flex-wrap">
                    <ModelSelector onModelChange={handleModelChange} />
                    <div className="flex-1 md:flex-none min-w-0">
                      <DiagramTypeSelector 
                        value={diagramType} 
                        onChange={handleDiagramTypeChange} 
                      />
                    </div>
                  </div>
                </div>
                
                {/* 主内容区域 */}
                <div className="flex-1 flex flex-col overflow-hidden mt-2 md:mt-4">
                  {/* 输入区域 - 固定高度（压缩以为“继续优化”留空间） */}
                  <div className="h-28 md:h-40 flex-shrink-0">
                    <TabsContent value="manual" className="h-full mt-0">
                      <TextInput 
                        value={inputText} 
                        onChange={handleTextChange} 
                        maxChars={maxChars}
                      />
                    </TabsContent>
                    <TabsContent value="file" className="h-full mt-0">
                      <FileUpload onTextExtracted={handleFileTextExtracted} />
                    </TabsContent>
                    <TabsContent value="history" className="h-full mt-0">
                      <HistoryList
                        items={historyEntries}
                        onSelect={(item) => {
                          setInputText(item.inputText);
                          setMermaidCode(item.mermaidCode);
                          setLeftTab("manual");
                        }}
                      />
                    </TabsContent>
                  </div>

                  {/* 生成按钮 - 固定高度 */}
                  <div className="h-16 flex items-center gap-2 flex-shrink-0">
                    <Button 
                      onClick={handleGenerateClick} 
                      disabled={isGenerating || !inputText.trim() || !isWithinCharLimit(inputText, maxChars)}
                      className="h-10 flex-1"
                    >
                      {isGenerating ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-background mr-2"></div>
                          生成中...
                        </>
                      ) : (
                        <>
                          <Wand2 className="mr-2 h-4 w-4" />
                          生成图表
                        </>
                      )}
                    </Button>
                    <div className="flex items-center">
                      <Switch 
                        checked={showRealtime} 
                        onCheckedChange={setShowRealtime}
                        title="实时生成"
                      />
                    </div>
                  </div>
                  
                  {/* 编辑器区域 - 占用剩余空间 */}
                  <div className="flex-1 min-h-0">
                    <MermaidEditor
                      code={mermaidCode}
                      onChange={handleMermaidCodeChange}
                      streamingContent={streamingContent}
                      isStreaming={isStreaming}
                      errorMessage={errorMessage}
                      hasError={hasError}
                      onStreamChunk={handleStreamChunk}
                      showRealtime={showRealtime}
                    />
                  </div>
                </div>
              </Tabs>
            </div>
            
            {/* 右侧面板 */}
            <div className={`${
              isLeftPanelCollapsed ? 'col-span-1' : 'col-span-1 md:col-span-2'
            } flex flex-col h-full overflow-hidden`}>
              {/* 控制按钮栏 - 固定高度 */}
              <div className="h-12 flex justify-between items-center flex-shrink-0">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={toggleLeftPanel}
                  className="h-9"
                >
                  {isLeftPanelCollapsed ? (
                    <>
                      <PanelLeftOpen className="h-4 w-4" />
                      <span className="hidden sm:inline ml-2">显示</span>
                    </>
                  ) : (
                    <>
                      <PanelLeftClose className="h-4 w-4" />
                      <span className="hidden sm:inline ml-2">隐藏</span>
                    </>
                  )}
                </Button>

                <div className="flex items-center gap-3">
                  {/* 渲染器选择改为 Switch */}
                  <div className="flex items-center gap-2">
                    {/* <span className="text-sm text-muted-foreground hidden sm:inline">渲染器</span> */}
                    <Switch
                      checked={renderMode === "mermaid"}
                      onCheckedChange={(checked) => setRenderMode(checked ? "mermaid" : "excalidraw")}
                      title="切换渲染器：Excalidraw / Mermaid"
                    />
                    <span className="text-xs text-muted-foreground">
                      {renderMode === "mermaid" ? "Mermaid" : "Excalidraw"}
                    </span>
                  </div>

                  {/* <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      window.dispatchEvent(new CustomEvent('resetView'));
                    }}
                    className="h-9"
                    title="重置视图"
                  >
                    <RotateCcw className="h-4 w-4" />
                  </Button> */}

                  {/* 全屏按钮已移除 */}
                </div>
              </div>

              {/* 渲染器区域 - 占用剩余空间 */}
              <div className="flex-1 min-h-0 mt-4" style={{ minHeight: '600px' }}>
                {renderMode === "excalidraw" ? (
                  <ExcalidrawRenderer
                    mermaidCode={mermaidCode}
                    onErrorChange={handleErrorChange}
                  />
                ) : (
                  <MermaidRenderer
                    mermaidCode={mermaidCode}
                    onChange={handleMermaidCodeChange}
                    onErrorChange={handleErrorChange}
                  />
                )}
              </div>
            </div>
          </div>
        </div>
      </main>
      
      <footer className="h-12 border-t flex items-center justify-center flex-shrink-0">
        <div className="text-center text-sm text-muted-foreground">
          AI 驱动的文本转 Mermaid 图表 Web 应用 &copy; {new Date().getFullYear()}
        </div>
      </footer>

      {/* Settings Dialog */}
      <SettingsDialog 
        open={showSettingsDialog} 
        onOpenChange={setShowSettingsDialog}
        onPasswordVerified={handlePasswordVerified}
        onConfigUpdated={handleConfigUpdated}
      />

      {/* Contact Dialog */}
      <Dialog open={showContactDialog} onOpenChange={setShowContactDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>联系作者</DialogTitle>
            <DialogDescription>
              <div className="py-4">
                <p className="mb-2">如需更多使用次数或技术支持，请扫描下方二维码联系作者（注明目的）</p>
                <div className="flex justify-center my-4">
                  <img src="/qrcode.png" alt="联系二维码" className="w-48" />
                </div>
                <p className="text-sm text-muted-foreground">
                  提示：您也可以在设置中配置自己的AI服务密钥，即可享有无限使用权限
                </p>
              </div>
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="sm:justify-center">
            <Button variant="secondary" onClick={() => setShowContactDialog(false)}>
              关闭
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Usage Limit Dialog */}
      <Dialog open={showLimitDialog} onOpenChange={setShowLimitDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>使用次数已达上限</DialogTitle>
            <DialogDescription>
              <div className="py-4">
                <p className="mb-2">您今日的使用次数已达上限 ({usageLimit}次/天)</p>
                <p className="mb-4">如需更多使用次数，您可以：</p>
                <ul className="list-disc list-inside space-y-2 text-sm mb-4">
                  <li>扫描下方二维码联系作者（注明目的）</li>
                  <li>在设置中配置您自己的AI服务密钥</li>
                </ul>
                <div className="flex justify-center my-4">
                  <img src="/qrcode.png" alt="联系二维码" className="w-48" />
                </div>
              </div>
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="sm:justify-center">
            <Button variant="secondary" onClick={() => setShowLimitDialog(false)}>
              关闭
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
