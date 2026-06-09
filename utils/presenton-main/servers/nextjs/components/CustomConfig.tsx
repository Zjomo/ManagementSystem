"use client";
import { useEffect, useState } from "react";
import { Check, ChevronsUpDown, Loader2 } from "lucide-react";
import { Button } from "./ui/button";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "./ui/command";
import { Popover, PopoverContent, PopoverTrigger } from "./ui/popover";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { getApiUrl } from "@/utils/api";
import { Switch } from "./ui/switch";

interface CustomConfigProps {
  customLlmUrl: string;
  customLlmApiKey: string;
  customModel: string;
  disableThinking: boolean;
  onInputChange: (value: string | boolean, field: string) => void;
}

export default function CustomConfig({
  customLlmUrl,
  customLlmApiKey,
  customModel,
  disableThinking,
  onInputChange,
}: CustomConfigProps) {
  const [customModels, setCustomModels] = useState<string[]>([]);
  const [customModelsLoading, setCustomModelsLoading] = useState(false);
  const [customModelsChecked, setCustomModelsChecked] = useState(false);
  const [openModelSelect, setOpenModelSelect] = useState(false);

  useEffect(() => {
    setCustomModels([]);
    setCustomModelsChecked(false);
  }, [customLlmUrl, customLlmApiKey]);

  const onUrlChange = (value: string) => {
    onInputChange(value, "custom_llm_url");
  };

  const onApiKeyChange = (value: string) => {
    onInputChange(value, "custom_llm_api_key");
  };

  const fetchCustomModels = async () => {
    if (!customLlmUrl) return;

    try {
      setCustomModelsLoading(true);
      const response = await fetch(getApiUrl("/api/v1/ppt/openai/models/available"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          url: customLlmUrl,
          api_key: customLlmApiKey,
          allow_empty_on_error: true,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        const normalizedModels = Array.isArray(data)
          ? data.filter((model): model is string => typeof model === "string")
          : [];
        setCustomModels(normalizedModels);
        setCustomModelsChecked(true);
        if (normalizedModels.length === 0) {
          toast.info("Model list unavailable. Enter the custom model name manually.");
        }
      } else {
        setCustomModels([]);
        setCustomModelsChecked(true);
        toast.info("Model list unavailable. Enter the custom model name manually.");
      }
    } catch (error) {
      console.error("Error fetching custom models:", error);
      toast.info("Model list unavailable. Enter the custom model name manually.");
      setCustomModels([]);
      setCustomModelsChecked(true);
    } finally {
      setCustomModelsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* URL Input */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          OpenAI Compatible URL
        </label>
        <div className="relative">
          <input
            type="text"
            required
            placeholder="Enter your URL"
            className="w-full px-4 py-2.5 outline-none border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors"
            value={customLlmUrl}
            onChange={(e) => onUrlChange(e.target.value)}
          />
        </div>
      </div>

      {/* API Key Input */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          OpenAI Compatible API Key
        </label>
        <div className="relative">
          <input
            type="text"
            required
            placeholder="Enter your API Key"
            className="w-full px-4 py-2.5 outline-none border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors"
            value={customLlmApiKey}
            onChange={(e) => onApiKeyChange(e.target.value)}
          />
        </div>
      </div>

      {/* Check for available models button - show when no models checked or no models found */}
      {(!customModelsChecked || (customModelsChecked && customModels.length === 0)) && (
        <div className="mb-4">
          <button
            onClick={fetchCustomModels}
            disabled={customModelsLoading || !customLlmUrl}
            className={`w-full py-2.5 px-4 rounded-lg transition-all duration-200 border-2 ${customModelsLoading || !customLlmUrl
              ? "bg-gray-100 border-gray-300 cursor-not-allowed text-gray-500"
              : "bg-white border-blue-600 text-blue-600 hover:bg-blue-50 focus:ring-2 focus:ring-blue-500/20"
              }`}
          >
            {customModelsLoading ? (
              <div className="flex items-center justify-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                Checking for models...
              </div>
            ) : (
              "Check for available models"
            )}
          </button>
        </div>
      )}

      {/* Show manual model input if no models were returned */}
      {customModelsChecked && customModels.length === 0 && (
        <div className="mb-4 space-y-3">
          <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <p className="text-sm text-yellow-800">
              No models were returned by this custom endpoint. Enter the model name manually.
            </p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Model Name
            </label>
            <input
              type="text"
              required
              placeholder="e.g. gpt-5.5"
              className="w-full px-4 py-2.5 outline-none border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors"
              value={customModel}
              onChange={(e) => onInputChange(e.target.value, "custom_model")}
            />
          </div>
        </div>
      )}

      {/* Model selection dropdown - only show if models are available */}
      {customModelsChecked && customModels.length > 0 && (
        <div className="mb-4">
          <div className="mb-3 p-3 bg-amber-50 border border-amber-200 rounded-lg">
            <p className="text-sm text-amber-800">
              <strong>Important:</strong> Only models with structured
              JSON schema output support will work reliably.
            </p>
          </div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Model
          </label>
          <div className="w-full">
            <Popover
              open={openModelSelect}
              onOpenChange={setOpenModelSelect}
            >
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  role="combobox"
                  aria-expanded={openModelSelect}
                  className="w-full h-12 px-4 py-4 outline-none border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors hover:border-gray-400 justify-between"
                >
                  <span className="text-sm font-medium text-gray-900">
                    {customModel || "Select a model"}
                  </span>
                  <ChevronsUpDown className="w-4 h-4 text-gray-500" />
                </Button>
              </PopoverTrigger>
              <PopoverContent
                className="p-0"
                align="start"
                style={{ width: "var(--radix-popover-trigger-width)" }}
              >
                <Command>
                  <CommandInput placeholder="Search model..." />
                  <CommandList>
                    <CommandEmpty>No model found.</CommandEmpty>
                    <CommandGroup>
                      {customModels.map((model, index) => (
                        <CommandItem
                          key={index}
                          value={model}
                          onSelect={(value) => {
                            onInputChange(value, "custom_model");
                            setOpenModelSelect(false);
                          }}
                        >
                          <Check
                            className={cn(
                              "mr-2 h-4 w-4",
                              customModel === model
                                ? "opacity-100"
                                : "opacity-0"
                            )}
                          />
                          <span className="text-sm font-medium text-gray-900">
                            {model}
                          </span>
                        </CommandItem>
                      ))}
                    </CommandGroup>
                  </CommandList>
                </Command>
              </PopoverContent>
            </Popover>
          </div>
        </div>
      )}
      {/* Disable Thinking Toggle */}
      <div>
        <div className="flex items-center justify-between mb-4 bg-green-50 p-2 rounded-sm">
          <label className="text-sm font-medium text-gray-700">
            Disable Thinking
          </label>
          <Switch
            checked={disableThinking}
            onCheckedChange={(checked) => onInputChange(checked, "disable_thinking")}
          />
        </div>
        <p className="mt-2 text-sm text-gray-500 flex items-center gap-2">
          <span className="block w-1 h-1 rounded-full bg-gray-400"></span>
          If enabled, Thinking will be disabled.
        </p>
      </div>
    </div >
  );
}
