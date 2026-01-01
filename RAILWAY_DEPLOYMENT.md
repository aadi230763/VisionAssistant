# Railway.app Deployment Guide

This guide will walk you through deploying your Vision-to-Voice Assistant on Railway.app with full MiDaS depth estimation support.

## Why Railway?

Railway's free tier provides:
- **8GB RAM** (vs Render's 512MB)
- **8 vCPUs** shared
- **$5 free credit monthly**
- **500 hours execution time/month**

This is sufficient for running YOLO11 + MiDaS depth estimation + PyTorch stack.

## Prerequisites

1. GitHub account with your code pushed
2. Railway account (sign up at https://railway.app/)
3. Environment variables ready:
   - `GEMINI_API_KEY`
   - `ELEVENLABS_API_KEY`
   - `ELEVENLABS_VOICE_ID`

## Backend Deployment Steps

### 1. Create Railway Project

1. Go to https://railway.app/
2. Click **"Start a New Project"**
3. Select **"Deploy from GitHub repo"**
4. Authorize Railway to access your GitHub
5. Select your repository: `vision` (or whatever you named it)

### 2. Configure Environment Variables

Once the project is created:

1. Click on your service
2. Go to **"Variables"** tab
3. Add these environment variables:

```env
GEMINI_API_KEY=your_gemini_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
ELEVENLABS_VOICE_ID=your_voice_id_here
YOLO_MODEL=yolo11m.pt
USE_DEPTH_ESTIMATION=true
USE_BROWSER_CAMERA=false
PORT=8000
```

### 3. Deploy

1. Railway will automatically detect the Dockerfile and start building
2. Wait for the build to complete (~5-10 minutes for first build)
3. Once deployed, you'll see a green checkmark
4. Click **"Settings"** → **"Generate Domain"** to get a public URL
5. Your backend will be available at: `https://your-app-name.up.railway.app`

### 4. Note Your WebSocket URL

Your WebSocket URL will be:
```
wss://your-app-name.up.railway.app
```

You'll need this for the frontend deployment.

## Frontend Deployment (Vercel)

### 1. Create `.env.production` in `ui/` folder

```env
REACT_APP_WS_URL=wss://your-app-name.up.railway.app
```

Replace `your-app-name.up.railway.app` with your actual Railway domain.

### 2. Deploy to Vercel

1. Go to https://vercel.com/
2. Click **"Add New Project"**
3. Import your GitHub repository
4. Set **"Root Directory"** to `ui`
5. Vercel will auto-detect React and configure build settings
6. Add environment variable:
   - Key: `REACT_APP_WS_URL`
   - Value: `wss://your-app-name.up.railway.app`
7. Click **"Deploy"**

### 3. Access Your App

Once deployed, Vercel will give you a URL like:
```
https://your-project.vercel.app
```

Open this in your browser and grant camera permissions!

## Testing

1. Open your Vercel URL
2. Grant camera permission when prompted
3. Click **"Start Camera"**
4. You should see:
   - Real-time object detection
   - Distance information (close, moderate, far)
   - Voice guidance every 10 seconds
   - Multiple people detected individually

## Monitoring

### Railway Logs
- Go to your Railway project
- Click on your service
- View **"Deployments"** tab
- Click on active deployment to see logs

### Common Issues

1. **"Out of memory" error**
   - Railway free tier should handle yolo11m + MiDaS
   - If issues persist, downgrade to `yolo11s.pt` in environment variables

2. **WebSocket connection failed**
   - Check that `REACT_APP_WS_URL` uses `wss://` (not `ws://`)
   - Verify Railway domain is correct
   - Check Railway logs for backend errors

3. **Model download timeout**
   - First deployment may take 10-15 minutes
   - YOLO11m and MiDaS models are downloaded during build
   - Subsequent deploys use cached models (~2-3 minutes)

## Cost Management

Railway free tier includes $5/month credit:
- Monitor usage at https://railway.app/account/usage
- Typical usage: ~$3-4/month for moderate testing
- Production use may require paid plan ($5/month minimum)

## Alternative: Deploy Frontend on Railway Too

You can also deploy the frontend on Railway:

1. Create a new service in the same project
2. Select your repository again
3. Set **"Root Directory"** to `ui`
4. Add environment variable `REACT_APP_WS_URL`
5. Railway will auto-detect npm and build React

This keeps everything in one place but uses more resources.

## Next Steps

- Test thoroughly with different objects and distances
- Monitor Railway usage to stay within free tier
- Consider upgrading if you exceed free limits
- Submit your hackathon with the Vercel URL! 🎉

## Rollback Instructions

If deployment fails:

1. Go to Railway **"Deployments"** tab
2. Click on a previous working deployment
3. Click **"Redeploy"**

Or update environment variables:
- Set `USE_DEPTH_ESTIMATION=false`
- Set `YOLO_MODEL=yolo11n.pt`
- Redeploy for lighter resource usage
