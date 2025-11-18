import React from 'react';
import { GitPullRequest, CheckCircle, XCircle, Clock } from 'lucide-react';

function Fixes() {
  // This would fetch real data from the API
  const mockFixes = [
    {
      id: '1',
      title: 'Fix memory leak in log processor',
      status: 'merged',
      pr_number: 123,
      created_at: '2024-01-15T10:30:00Z',
      severity: 'high',
    },
    {
      id: '2',
      title: 'Add connection pool limits',
      status: 'open',
      pr_number: 124,
      created_at: '2024-01-16T14:20:00Z',
      severity: 'medium',
    },
  ];

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'merged':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'closed':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Clock className="h-5 w-5 text-yellow-500" />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 text-red-800';
      case 'high':
        return 'bg-orange-100 text-orange-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-blue-100 text-blue-800';
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Fixes & Pull Requests</h1>
        <p className="mt-2 text-sm text-gray-600">
          Auto-generated fixes and their status
        </p>
      </div>

      <div className="bg-white shadow rounded-lg overflow-hidden">
        <ul className="divide-y divide-gray-200">
          {mockFixes.map((fix) => (
            <li key={fix.id} className="p-6 hover:bg-gray-50">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4 flex-1">
                  <GitPullRequest className="h-6 w-6 text-gray-400" />
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <h3 className="text-lg font-medium text-gray-900">{fix.title}</h3>
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getSeverityColor(
                          fix.severity
                        )}`}
                      >
                        {fix.severity}
                      </span>
                    </div>
                    <div className="mt-1 flex items-center space-x-4 text-sm text-gray-500">
                      <span>PR #{fix.pr_number}</span>
                      <span>•</span>
                      <span>{new Date(fix.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  {getStatusIcon(fix.status)}
                  <span className="text-sm font-medium capitalize text-gray-700">
                    {fix.status}
                  </span>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>

      {mockFixes.length === 0 && (
        <div className="text-center py-12 bg-white shadow rounded-lg">
          <GitPullRequest className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No fixes yet</h3>
          <p className="mt-1 text-sm text-gray-500">
            Fixes will appear here when issues are detected and resolved.
          </p>
        </div>
      )}
    </div>
  );
}

export default Fixes;
