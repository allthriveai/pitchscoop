import asyncio
import redis.asyncio as redis
import json

async def check_latest():
    client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)
    
    # Find the most recent session
    keys = await client.keys('event:*:session:*')
    if keys:
        latest_key = sorted(keys)[-1]
        print(f'Latest session key: {latest_key}')
        
        data = await client.get(latest_key)
        if data:
            session = json.loads(data)
            print(f'Session ID: {session.get("session_id")}')
            print(f'Status: {session.get("status")}')
            
            transcript = session.get('final_transcript', {})
            print(f'Has final_transcript: {bool(transcript)}')
            if transcript:
                text = transcript.get('total_text', '')
                print(f'Transcript text length: {len(text)}')
                if text:
                    print(f'First 100 chars: {text[:100]}')
                else:
                    print('Transcript text is EMPTY')
                print(f'Segments count: {transcript.get("segments_count", 0)}')
            else:
                print('No final_transcript field')
    else:
        print('No sessions found')
    
    await client.close()

if __name__ == '__main__':
    asyncio.run(check_latest())