export interface ServiceConfig {
  id: string;
  name: string;
  description: string;
  port: number;
  path?: string;
  healthCheck: string;
  category: ServiceCategory;
  icon: string;
  critical: boolean;
}

export interface Service extends ServiceConfig {
  status: 'healthy' | 'warning' | 'error' | 'unknown';
  responseTime?: number;
  lastCheck?: Date;
  uptime?: number;
  errorMessage?: string;
  metrics?: ServiceMetrics;
  url?: string;
}

export interface ServiceStatus {
  id: string;
  status: 'healthy' | 'warning' | 'error' | 'unknown';
  responseTime: number;
  lastCheck: Date;
  uptime?: number;
  errorMessage?: string;
  metrics?: ServiceMetrics;
}

export interface ServiceMetrics {
  cpu?: number;
  memory?: number;
  connections?: number;
  requests?: number;
  errors?: number;
}

export interface DashboardConfig {
  refreshInterval: number;
  showMetrics: boolean;
  autoRefresh: boolean;
  theme: 'dark' | 'light';
}

export type ServiceCategory = 
  | 'database' 
  | 'cache' 
  | 'automation' 
  | 'ai' 
  | 'monitoring' 
  | 'web' 
  | 'api'
  | 'external';

export interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'viewer';
}
