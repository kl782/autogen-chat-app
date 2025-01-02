import { NextResponse } from 'next/server';
import { put } from '@vercel/blob';
import { Configuration, OpenAIApi } from 'openai';
import autogen from 'autogen';

// Initialize OpenAI
const config = new Configuration({
  apiKey: process.env.OPENAI_API_KEY,
});
const openai = new OpenAIApi(config);

export async function POST(req: Request) {
  try {
    const { message } = await req.json();

    // Initialize AutoGen config
    const config_list = [{
      model: 'gpt-4',
      api_key: process.env.OPENAI_API_KEY
    }];

    // Create assistant agent
    const assistant = new autogen.AssistantAgent(
      'assistant',
      {
        llm_config: {
          config_list,
          temperature: 0.7,
        }
      }
    );

    // Get response from AutoGen
    const response = await assistant.getResponse(message);
    let imageUrl = null;
    let audioUrl = null;

    // Generate image if requested
    if (message.toLowerCase().includes('generate') && message.toLowerCase().includes('image')) {
      const imageResponse = await openai.createImage({
        prompt: message,
        n: 1,
        size: '1024x1024',
      });
      
      // Upload image to Vercel Blob Storage
      const imageBlob = await fetch(imageResponse.data.data[0].url).then(r => r.blob());
      const { url } = await put(`images/${Date.now()}.png`, imageBlob, {
        access: 'public',
      });
      imageUrl = url;
    }

    // Generate speech from response
    const speechResponse = await openai.audio.speech.create({
      model: "tts-1",
      voice: "alloy",
      input: response.text,
    });

    // Upload audio to Vercel Blob Storage
    const audioBlob = await speechResponse.blob();
    const { url: audioUrl } = await put(`audio/${Date.now()}.mp3`, audioBlob, {
      access: 'public',
    });

    return NextResponse.json({
      text: response.text,
      imageUrl,
      audioUrl,
    });

  } catch (error) {
    console.error('Error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}