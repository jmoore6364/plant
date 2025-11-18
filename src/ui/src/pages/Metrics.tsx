import React from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { Activity, Cpu, HardDrive, MemoryStick } from 'lucide-react';

const API_URL = 'http://localhost:8000';

function Metrics() {
  const { data: detailed } = useQuery({
    queryKey: ['detailed-metrics'],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/metrics/detailed`);
      return response.data;
    },
    refetchInterval: 5000,
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">System Metrics</h1>
        <p className="mt-2 text-sm text-gray-600">
          Detailed system resource information
        </p>
      </div>

      {detailed && (
        <>
          {/* Base Metrics */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Current Metrics</h2>
            <div className="grid grid-cols-2 gap-4">
              <MetricDetail
                icon={<Cpu className="h-5 w-5" />}
                label="CPU Usage"
                value={`${detailed.base_metrics.cpu_percent.toFixed(1)}%`}
              />
              <MetricDetail
                icon={<MemoryStick className="h-5 w-5" />}
                label="Memory Usage"
                value={`${detailed.base_metrics.memory_percent.toFixed(1)}%`}
              />
              <MetricDetail
                icon={<HardDrive className="h-5 w-5" />}
                label="Disk Usage"
                value={`${detailed.base_metrics.disk_usage_percent.toFixed(1)}%`}
              />
              <MetricDetail
                icon={<Activity className="h-5 w-5" />}
                label="Processes"
                value={detailed.base_metrics.process_count}
              />
            </div>
          </div>

          {/* Top CPU Processes */}
          {detailed.top_cpu_processes && (
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">Top CPU Processes</h2>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        PID
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Name
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        CPU %
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Memory %
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {detailed.top_cpu_processes.slice(0, 10).map((proc: any) => (
                      <tr key={proc.pid}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {proc.pid}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {proc.name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {proc.cpu_percent?.toFixed(1) || '0.0'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {proc.memory_percent?.toFixed(1) || '0.0'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Network Connections */}
          {detailed.network_connections && Object.keys(detailed.network_connections).length > 0 && (
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">Network Connections</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(detailed.network_connections).map(([state, count]) => (
                  <div key={state} className="bg-gray-50 p-4 rounded-md">
                    <p className="text-sm font-medium text-gray-500">{state}</p>
                    <p className="text-2xl font-semibold text-gray-900">{count as number}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function MetricDetail({ icon, label, value }: any) {
  return (
    <div className="flex items-center space-x-3 bg-gray-50 p-4 rounded-md">
      <div className="flex-shrink-0 text-blue-600">{icon}</div>
      <div>
        <p className="text-sm font-medium text-gray-500">{label}</p>
        <p className="text-xl font-semibold text-gray-900">{value}</p>
      </div>
    </div>
  );
}

export default Metrics;
