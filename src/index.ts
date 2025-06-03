import { Bot, webhookCallback } from 'grammy';
import express, { Request, Response } from 'express';
import dotenv from 'dotenv';
import pino from 'pino';

// Load environment variables
dotenv.config();

// Initialize logger
const logger = pino({
  transport: {
    target: 'pino-pretty',
    options: {
      colorize: true,
    },
  },
});

// Validate required environment variables
const requiredEnvVars = ['TELEGRAM_TOKEN', 'OPENAI_API_KEY'];
for (const envVar of requiredEnvVars) {
  if (!process.env[envVar]) {
    logger.error(`Missing required environment variable: ${envVar}`);
    process.exit(1);
  }
}

// Initialize bot
const bot = new Bot(process.env.TELEGRAM_TOKEN as string);

// Initialize express app
const app = express();
app.use(express.json());

// Health check endpoint
app.get('/', (_req: Request, res: Response) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Set up webhook handling
if (process.env.NODE_ENV === 'production') {
  const webhookUrl = process.env.WEBHOOK_URL;
  if (!webhookUrl) {
    logger.error('WEBHOOK_URL is required in production mode');
    process.exit(1);
  }
  
  app.use('/webhook', webhookCallback(bot, 'express'));
  bot.api.setWebhook(webhookUrl + '/webhook').then(() => {
    logger.info(`Webhook set to ${webhookUrl}/webhook`);
  });
} else {
  // Use long polling in development
  bot.start({
    onStart: () => logger.info('Bot started using long polling'),
  });
}

// Start the server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  logger.info(`Server is running on port ${PORT}`);
}); 