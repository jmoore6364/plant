import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Activity, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import axios from 'axios';

const API_URL = 'http://localhost:8000';

function Dashboard() {
  const { data: metrics } = useQuery({
    queryKey: ['current-metrics'],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/metrics/current`);
      return response.data;
    },
    refetchInterval: 5000,
  });

  const { data: issues } = useQuery({
    queryKey: ['resource-issues'],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/metrics/issues`);
      return response.data;
    },
    refetchInterval: 5000,
  });

  const { data: history } = useQuery({
    queryKey: ['metrics-history'],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/metrics/history?limit=50`);
      return response.data.metrics;
    },
    refetchInterval: 10000,
  });

  const getStatusColor = (value: number, warning: number, critical: number) => {
    if (value >= critical) return 'text-red-600 bg-red-100';
    if (value >= warning) return 'text-yellow-600 bg-yellow-100';
    return 'text-green-600 bg-green-100';
  };

  const getStatusIcon = (value: number, warning: number, critical: number) => {
    if (value >= critical) return <XCircle className="h-5 w-5" />;
    if (value >= warning) return <AlertTriangle className="h-5 w-5" />;
    return <CheckCircle className="h-5 w-5" />;
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">System Health Dashboard</h1>
        <p className="mt-2 text-sm text-gray-600">
          Real-time monitoring and AI-powered analysis
        </p>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="CPU Usage"
          value={metrics?.cpu_percent}
          unit="%"
          icon={<Activity />}
          status={getStatusColor(metrics?.cpu_percent || 0, 70, 90)}
          statusIcon={getStatusIcon(metrics?.cpu_percent || 0, 70, 90)}
        />
        <MetricCard
          title="Memory Usage"
          value={metrics?.memory_percent}
          unit="%"
          icon={<Activity />}
          status={getStatusColor(metrics?.memory_percent || 0, 70, 85)}
          statusIcon={getStatusIcon(metrics?.memory_percent || 0, 70, 85)}
        />
        <MetricCard
          title="Disk Usage"
          value={metrics?.disk_usage_percent}
          unit="%"
          icon={<Activity />}
          status={getStatusColor(metrics?.disk_usage_percent || 0, 80, 90)}
          statusIcon={getStatusIcon(metrics?.disk_usage_percent || 0, 80, 90)}
        />
        <MetricCard
          title="Processes"
          value={metrics?.process_count}
          unit=""
          icon={<Activity />}
          status="text-blue-600 bg-blue-100"
          statusIcon={<CheckCircle className="h-5 w-5" />}
        />
      </div>

      {/* Issues Alert */}
      {issues && issues.count > 0 && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4">
          <div className="flex">
            <AlertTriangle className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">
                {issues.count} Resource Issue{issues.count > 1 ? 's' : ''} Detected
              </h3>
              <div className="mt-2 text-sm text-red-700">
                <ul className="list-disc list-inside space-y-1">
                  {issues.issues.map((issue: any, idx: number) => (
                    <li key={idx}>{issue.message}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium text-gray-900 mb-4">CPU & Memory Trends</h3>
          {history && history.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={history}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                />
                <YAxis />
                <Tooltip
                  labelFormatter={(value) => new Date(value).toLocaleString()}
                />
                <Line
                  type="monotone"
                  dataKey="cpu_percent"
                  stroke="#3b82f6"
                  name="CPU %"
                />
                <Line
                  type="monotone"
                  dataKey="memory_percent"
                  stroke="#10b981"
                  name="Memory %"
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-64 text-gray-400">
              No data available
            </div>
          )}
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Disk Usage Trend</h3>
          {history && history.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={history}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                />
                <YAxis />
                <Tooltip
                  labelFormatter={(value) => new Date(value).toLocaleString()}
                />
                <Line
                  type="monotone"
                  dataKey="disk_usage_percent"
                  stroke="#f59e0b"
                  name="Disk %"
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-64 text-gray-400">
              No data available
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function MetricCard({ title, value, unit, icon, status, statusIcon }: any) {
  return (
    <div className="bg-white overflow-hidden shadow rounded-lg">
      <div className="p-5">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <div className={`rounded-md p-3 ${status}`}>
              {icon}
            </div>
          </div>
          <div className="ml-5 w-0 flex-1">
            <dl>
              <dt className="text-sm font-medium text-gray-500 truncate">{title}</dt>
              <dd className="flex items-baseline">
                <div className="text-2xl font-semibold text-gray-900">
                  {value !== undefined ? value.toFixed(1) : '--'}
                  <span className="text-sm text-gray-500 ml-1">{unit}</span>
                </div>
                <div className="ml-2">{statusIcon}</div>
              </dd>
            </dl>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
