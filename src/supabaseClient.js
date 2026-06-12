import { createClient } from '@supabase/supabase-js';

const supabaseUrl = 'https://livutwczkxpuyqiupcpf.supabase.co';
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxpdnV0d2N6a3hwdXlxaXVwY3BmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODEyMDgzNjYsImV4cCI6MjA5Njc4NDM2Nn0.qzqCoFxpuKK08DTh1HJsk5Q5e23-NH_zWSzTtNbZEGM';

export const supabase = createClient(supabaseUrl, supabaseAnonKey);