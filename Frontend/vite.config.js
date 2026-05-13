import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  return {
    plugins: [react()],
    publicDir: "Public",
    server: {
      host: "0.0.0.0",
      port: 5173,
      allowedHosts: ["intranetatg.durgaaisolutions.in"],
      proxy: {
        '/api': {
          target: env.VITE_BACKEND_URL || 'http://Backend:8000',
          changeOrigin: true,
          secure: false,
          rewrite: (path) => path.replace(/^\/api/, ''),
          configure: (proxy, _options) => {
            proxy.on('error', (err, _req, _res) => {
              console.log('proxy error', err);
            });
            proxy.on('proxyReq', (proxyReq, req, _res) => {
              console.log('Sending Request To The Target:', req.method, req.url);
            });
            proxy.on('proxyRes', (proxyRes, req, _res) => {
              console.log('Received Response From The Target:', proxyRes.statusCode, req.url);
            });
          },
        }
      },
      cors: true,
    },
    define: {
      'import.meta.env.VITE_API_BASE_URL': JSON.stringify(env.VITE_API_BASE_URL || '/api'),
    },
    build: {
      outDir: 'dist',
      sourcemap: true,
      rollupOptions: {
        output: {
          manualChunks: (id) => {
            if (id.includes('node_modules')) {
              if (id.includes('react') || id.includes('react-dom')) {
                return 'vendor';
              }
              if (id.includes('lucide-react')) {
                return 'icons';
              }
              return 'vendor';
            }
          }
        }
      }
    }
  };
});