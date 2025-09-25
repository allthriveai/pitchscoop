#!/usr/bin/env python3

# This script patches the test page to use optimized audio constraints
# for better microphone audio quality

import sys
import re

def fix_audio_constraints():
    print('🔧 Fixing Browser Audio Constraints for Better Quality')
    print('=' * 55)
    
    # Read the current test page
    try:
        with open('/app/test_recording.html', 'r') as f:
            content = f.read()
        
        print('✅ Found test_recording.html')
    except FileNotFoundError:
        print('❌ test_recording.html not found')
        # Check if it's in main.py as embedded HTML
        try:
            with open('/app/main.py', 'r') as f:
                content = f.read()
            print('✅ Found main.py (embedded HTML)')
        except FileNotFoundError:
            print('❌ Could not find HTML content')
            return False
    
    # Find and replace the constraintOptions array with optimized settings
    old_constraints = r'const constraintOptions = \[\s*// Option 1: Strict constraints.*?\];'
    
    new_constraints = '''const constraintOptions = [
                    // Option 1: High-quality microphone optimized (NEW!)
                    {
                        deviceId: { exact: selectedDeviceId },
                        sampleRate: { ideal: 48000, min: 44100 }, // Higher sample rate
                        channelCount: 1,
                        echoCancellation: false,    // Disable for clearer speech
                        noiseSuppression: false,    // Disable for natural voice
                        autoGainControl: false,     // Disable for consistent levels
                        latency: { ideal: 0.01 },  // Low latency for better quality
                        volume: { ideal: 1.0 }     // Full volume
                    },
                    // Option 2: Medium quality fallback
                    {
                        deviceId: { ideal: selectedDeviceId },
                        sampleRate: { ideal: 44100 },
                        channelCount: 1,
                        echoCancellation: false,
                        noiseSuppression: false,
                        autoGainControl: true      // Enable AGC as fallback
                    },
                    // Option 3: Standard quality
                    {
                        deviceId: { ideal: selectedDeviceId },
                        sampleRate: { ideal: 16000 },
                        channelCount: 1,
                        echoCancellation: false,
                        noiseSuppression: false
                    },
                    // Option 4: Basic compatibility (original)
                    {
                        deviceId: { ideal: selectedDeviceId },
                        echoCancellation: true,
                        noiseSuppression: true
                    },
                    // Option 5: Minimal constraints
                    {
                        deviceId: { ideal: selectedDeviceId }
                    }
                ];'''
    
    # Apply the fix
    if 'constraintOptions' in content:
        # Use a more flexible regex that handles the multiline structure
        pattern = r'const constraintOptions = \[[\s\S]*?\];'
        updated_content = re.sub(pattern, new_constraints, content, flags=re.MULTILINE | re.DOTALL)
        
        if updated_content != content:
            # Write the updated content back
            if 'test_recording.html' in content:
                output_file = '/app/test_recording.html'
            else:
                output_file = '/app/main.py'
            
            with open(output_file, 'w') as f:
                f.write(updated_content)
            
            print('✅ Updated audio constraints for better quality!')
            print('📈 Improvements:')
            print('   - Higher sample rates (48kHz/44kHz preferred)')
            print('   - Disabled echo cancellation (clearer speech)')
            print('   - Disabled noise suppression (natural voice)')  
            print('   - Disabled auto-gain control (consistent levels)')
            print('   - Added low latency settings')
            print('   - Added volume optimization')
            return True
        else:
            print('⚠️  Pattern not found or no changes made')
            return False
    else:
        print('❌ constraintOptions not found in file')
        return False

if __name__ == '__main__':
    success = fix_audio_constraints()
    if success:
        print('\n🎯 Next Steps:')
        print('1. The browser page will reload automatically')
        print('2. Test your microphone again at http://localhost:8000/test')
        print('3. You should now get much better transcription quality!')
    else:
        print('\n❌ Fix failed - manual intervention needed')