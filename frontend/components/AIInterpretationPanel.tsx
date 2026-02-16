import React, { useState, useEffect } from 'react';
import { Brain, AlertTriangle, CheckCircle, Clock } from 'lucide-react';
import { MarketIntelligence } from '../engines/intelligenceEngine';

interface AIInterpretationPanelProps {
  intelligence?: MarketIntelligence;
}

interface AIInterpretation {
  narrative: string | null;
  risk_context: string | null;
  positioning_context: string | null;
  contradiction_flags: string[];
  confidence_tone: 'high' | 'medium' | 'cautious';
  interpreted_at?: string;
  fallback?: boolean;
}

export default function AIInterpretationPanel({ intelligence }: AIInterpretationPanelProps) {
  const [interpretation, setInterpretation] = useState<AIInterpretation | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!intelligence) {
      setInterpretation(null);
      return;
    }

    const fetchInterpretation = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const response = await fetch('/api/v1/intelligence/interpret', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(intelligence),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        setInterpretation(result.data);
        
      } catch (err) {
        console.error('Failed to fetch AI interpretation:', err);
        setError('AI interpretation temporarily unavailable');
      } finally {
        setLoading(false);
      }
    };

    fetchInterpretation();
  }, [intelligence]);

  const getConfidenceIcon = (tone: string) => {
    switch (tone) {
      case 'high':
        return <CheckCircle className="w-4 h-4 text-success-400" />;
      case 'medium':
        return <Brain className="w-4 h-4 text-warning-400" />;
      case 'cautious':
      default:
        return <AlertTriangle className="w-4 h-4 text-danger-400" />;
    }
  };

  const getConfidenceColor = (tone: string) => {
    switch (tone) {
      case 'high':
        return 'text-success-400 bg-success-500/20 border-success-500/30';
      case 'medium':
        return 'text-warning-400 bg-warning-500/20 border-warning-500/30';
      case 'cautious':
      default:
        return 'text-danger-400 bg-danger-500/20 border-danger-500/30';
    }
  };

  if (!intelligence) {
    return (
      <div className="glass-morphism rounded-2xl p-6 border border-white/10">
        <div className="flex items-center gap-3 mb-4">
          <Brain className="w-5 h-5 text-primary-400" />
          <h3 className="text-lg font-semibold text-white">AI Interpretation</h3>
        </div>
        <div className="text-center text-muted-foreground">
          <Clock className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p>Waiting for market intelligence...</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="glass-morphism rounded-2xl p-6 border border-white/10">
        <div className="flex items-center gap-3 mb-4">
          <Brain className="w-5 h-5 text-primary-400" />
          <h3 className="text-lg font-semibold text-white">AI Interpretation</h3>
        </div>
        <div className="text-center text-muted-foreground">
          <Brain className="w-8 h-8 mx-auto mb-2 animate-pulse" />
          <p>AI interpretation initializing...</p>
        </div>
      </div>
    );
  }

  if (error || !interpretation) {
    return (
      <div className="glass-morphism rounded-2xl p-6 border border-white/10">
        <div className="flex items-center gap-3 mb-4">
          <Brain className="w-5 h-5 text-primary-400" />
          <h3 className="text-lg font-semibold text-white">AI Interpretation</h3>
        </div>
        <div className="text-center text-muted-foreground">
          <AlertTriangle className="w-8 h-8 mx-auto mb-2" />
          <p>{error || 'AI interpretation temporarily unavailable'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="glass-morphism rounded-2xl p-6 border border-white/10">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Brain className="w-5 h-5 text-primary-400" />
          <h3 className="text-lg font-semibold text-white">AI Interpretation</h3>
        </div>
        <div className={`flex items-center gap-2 px-3 py-1 rounded-full border text-xs font-medium ${getConfidenceColor(interpretation.confidence_tone)}`}>
          {getConfidenceIcon(interpretation.confidence_tone)}
          <span className="capitalize">{interpretation.confidence_tone}</span>
        </div>
      </div>

      <div className="space-y-6">
        {/* Narrative */}
        {interpretation.narrative && (
          <div>
            <h4 className="text-sm font-medium text-white mb-2">Market Narrative</h4>
            <p className="text-sm text-muted-foreground leading-relaxed">
              {interpretation.narrative}
            </p>
          </div>
        )}

        {/* Risk Context */}
        {interpretation.risk_context && (
          <div>
            <h4 className="text-sm font-medium text-white mb-2">Risk Context</h4>
            <p className="text-sm text-muted-foreground leading-relaxed">
              {interpretation.risk_context}
            </p>
          </div>
        )}

        {/* Positioning Context */}
        {interpretation.positioning_context && (
          <div>
            <h4 className="text-sm font-medium text-white mb-2">Positioning Context</h4>
            <p className="text-sm text-muted-foreground leading-relaxed">
              {interpretation.positioning_context}
            </p>
          </div>
        )}

        {/* Contradiction Flags */}
        {interpretation.contradiction_flags && interpretation.contradiction_flags.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-white mb-2">Market Contradictions</h4>
            <div className="space-y-1">
              {interpretation.contradiction_flags.map((flag, index) => (
                <div key={index} className="flex items-center gap-2 text-sm text-warning-400">
                  <AlertTriangle className="w-3 h-3 flex-shrink-0" />
                  <span>{flag}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {interpretation.fallback && (
          <div className="text-center text-xs text-muted-foreground pt-4 border-t border-white/10">
            Using fallback interpretation
          </div>
        )}
      </div>
    </div>
  );
}
