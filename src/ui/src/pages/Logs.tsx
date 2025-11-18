import React, { useState } from 'react';
import { AlertCircle, FileText, Upload } from 'lucide-react';
import axios from 'axios';

const API_URL = 'http://localhost:8000';

function Logs() {
  const [logContent, setLogContent] = useState('');
  const [analysis, setAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleAnalyze = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_URL}/analyze`, {
        log_content: logContent,
        include_ai_analysis: true,
        auto_fix: false,
        auto_pr: false,
      });
      setAnalysis(response.data);
    } catch (error) {
      console.error('Analysis failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Log Analysis</h1>
        <p className="mt-2 text-sm text-gray-600">
          Analyze logs with AI-powered insights
        </p>
      </div>

      <div className="bg-white shadow rounded-lg p-6">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Paste Log Content
            </label>
            <textarea
              rows={10}
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-3 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Paste your logs here..."
              value={logContent}
              onChange={(e) => setLogContent(e.target.value)}
            />
          </div>

          <button
            onClick={handleAnalyze}
            disabled={!logContent || loading}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            <FileText className="h-4 w-4 mr-2" />
            {loading ? 'Analyzing...' : 'Analyze Logs'}
          </button>
        </div>
      </div>

      {analysis && (
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Analysis Results</h2>

          <div className="space-y-4">
            <div>
              <p className="text-sm text-gray-600">
                Analyzed {analysis.logs_analyzed} log entries in {analysis.processing_time_ms.toFixed(0)}ms
              </p>
            </div>

            {analysis.anomalies && analysis.anomalies.length > 0 && (
              <div>
                <h3 className="text-lg font-medium mb-2">Anomalies Detected</h3>
                <div className="space-y-2">
                  {analysis.anomalies.map((anomaly: any, idx: number) => (
                    <div key={idx} className="border-l-4 border-yellow-400 bg-yellow-50 p-4">
                      <div className="flex">
                        <AlertCircle className="h-5 w-5 text-yellow-400" />
                        <div className="ml-3">
                          <p className="text-sm font-medium text-yellow-800">
                            {anomaly.description}
                          </p>
                          <p className="text-sm text-yellow-700 mt-1">
                            Severity: {anomaly.severity} | Confidence: {(anomaly.confidence_score * 100).toFixed(0)}%
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {analysis.diagnoses && analysis.diagnoses.length > 0 && (
              <div>
                <h3 className="text-lg font-medium mb-2">AI Diagnosis</h3>
                {analysis.diagnoses.map((diagnosis: any, idx: number) => (
                  <div key={idx} className="bg-blue-50 p-4 rounded-md">
                    <h4 className="font-medium text-blue-900">{diagnosis.summary}</h4>
                    <p className="text-sm text-blue-800 mt-2">{diagnosis.root_cause}</p>
                    {diagnosis.recommendations && (
                      <div className="mt-3">
                        <p className="text-sm font-medium text-blue-900">Recommendations:</p>
                        <ul className="list-disc list-inside text-sm text-blue-800 mt-1">
                          {diagnosis.recommendations.map((rec: string, i: number) => (
                            <li key={i}>{rec}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default Logs;
