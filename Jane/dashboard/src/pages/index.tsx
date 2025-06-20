import { useState } from 'react';
import { useSession, signIn, signOut } from 'next-auth/react';
import { useQuery } from '@tanstack/react-query';
import Head from 'next/head';
import ServiceCard from '../components/ServiceCard';
import { Service } from '../types/dashboard';
import { ALL_SERVICES } from '../lib/services';
import { checkServiceHealth } from '../lib/healthCheck';

export default function Dashboard() {
  const { data: session, status } = useSession();
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(30); // seconds

  // Query for all service statuses
  const { data: serviceStatuses, refetch, isLoading, error } = useQuery({
    queryKey: ['serviceStatuses'],
    queryFn: async () => {
      const statusPromises = ALL_SERVICES.map(async (service) => {
        const status = await checkServiceHealth(service);
        return { ...service, ...status };
      });
      return Promise.all(statusPromises);
    },
    refetchInterval: autoRefresh ? refreshInterval * 1000 : false,
    refetchIntervalInBackground: true,
    staleTime: 15 * 1000, // 15 seconds
  });

  // Manual refresh handler
  const handleRefresh = () => {
    refetch();
  };

  // Authentication loading state
  if (status === 'loading') {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  // Require authentication
  if (!session) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="bg-gray-800 p-8 rounded-lg shadow-lg max-w-md w-full">
          <h1 className="text-2xl font-bold text-white mb-6 text-center">
            Service Dashboard
          </h1>
          <p className="text-gray-300 mb-6 text-center">
            Please sign in to access the service monitoring dashboard.
          </p>
          <button
            onClick={() => signIn()}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-4 rounded-lg transition-colors"
          >
            Sign In
          </button>
        </div>
      </div>
    );
  }

  // Calculate overall system health
  const totalServices = serviceStatuses?.length || 0;
  const healthyServices = serviceStatuses?.filter(s => s.status === 'healthy').length || 0;
  const unhealthyServices = serviceStatuses?.filter(s => s.status === 'unhealthy').length || 0;
  const unknownServices = serviceStatuses?.filter(s => s.status === 'unknown').length || 0;

  return (
    <>
      <Head>
        <title>Service Dashboard - Jane & Motoko</title>
        <meta name="description" content="Real-time service monitoring dashboard" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className="min-h-screen bg-gray-900 text-white">
        {/* Header */}
        <header className="bg-gray-800 border-b border-gray-700 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white">Service Dashboard</h1>
              <p className="text-gray-400">Jane (192.168.1.17) & Motoko (192.168.1.12)</p>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* Auto-refresh controls */}
              <div className="flex items-center space-x-2">
                <label className="flex items-center space-x-2 text-sm">
                  <input
                    type="checkbox"
                    checked={autoRefresh}
                    onChange={(e) => setAutoRefresh(e.target.checked)}
                    className="rounded bg-gray-700 border-gray-600 text-blue-600 focus:ring-blue-500"
                  />
                  <span>Auto-refresh</span>
                </label>
                
                <select
                  value={refreshInterval}
                  onChange={(e) => setRefreshInterval(Number(e.target.value))}
                  className="bg-gray-700 border border-gray-600 rounded px-2 py-1 text-sm"
                  disabled={!autoRefresh}
                >
                  <option value={15}>15s</option>
                  <option value={30}>30s</option>
                  <option value={60}>1m</option>
                  <option value={120}>2m</option>
                </select>
              </div>

              {/* Manual refresh button */}
              <button
                onClick={handleRefresh}
                disabled={isLoading}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center space-x-2"
              >
                <svg
                  className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                  />
                </svg>
                <span>Refresh</span>
              </button>

              {/* User menu */}
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-300">
                  {session.user?.email || 'User'}
                </span>
                <button
                  onClick={() => signOut()}
                  className="bg-gray-700 hover:bg-gray-600 px-3 py-2 rounded text-sm transition-colors"
                >
                  Sign Out
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* System Overview */}
        <div className="px-6 py-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <h3 className="text-lg font-semibold mb-2">Total Services</h3>
              <p className="text-3xl font-bold text-blue-400">{totalServices}</p>
            </div>
            
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <h3 className="text-lg font-semibold mb-2">Healthy</h3>
              <p className="text-3xl font-bold text-green-400">{healthyServices}</p>
            </div>
            
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <h3 className="text-lg font-semibold mb-2">Unhealthy</h3>
              <p className="text-3xl font-bold text-red-400">{unhealthyServices}</p>
            </div>
            
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <h3 className="text-lg font-semibold mb-2">Unknown</h3>
              <p className="text-3xl font-bold text-yellow-400">{unknownServices}</p>
            </div>
          </div>

          {/* Error message */}
          {error && (
            <div className="bg-red-900 border border-red-700 rounded-lg p-4 mb-6">
              <p className="text-red-200">
                Error loading service statuses: {error.message}
              </p>
            </div>
          )}

          {/* Services Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {serviceStatuses?.map((service) => (
              <ServiceCard key={service.name} service={service} />
            )) || (
              // Loading skeleton
              Array.from({ length: ALL_SERVICES.length }).map((_, i) => (
                <div key={i} className="bg-gray-800 rounded-lg p-6 border border-gray-700 animate-pulse">
                  <div className="h-6 bg-gray-700 rounded mb-4"></div>
                  <div className="h-4 bg-gray-700 rounded mb-2"></div>
                  <div className="h-4 bg-gray-700 rounded mb-2 w-2/3"></div>
                  <div className="h-4 bg-gray-700 rounded w-1/2"></div>
                </div>
              ))
            )}
          </div>

          {/* Last updated */}
          <div className="mt-8 text-center text-gray-400 text-sm">
            Last updated: {new Date().toLocaleString()}
          </div>
        </div>
      </div>
    </>
  );
}
