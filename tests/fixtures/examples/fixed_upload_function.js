        async function uploadRecording() {
            if (!recordedBlob) {
                updateStatus('No recording to upload!', 'error');
                return;
            }
            
            try {
                updateStatus('Uploading to PitchScoop...', 'warning');
                uploadBtn.disabled = true;
                
                const teamName = document.getElementById('teamName').value || 'Test Team';
                const pitchTitle = document.getElementById('pitchTitle').value || 'Browser Recording Test';
                const eventIdInput = document.getElementById('eventId').value.trim();
                
                let eventId;
                
                if (eventIdInput) {
                    // Use provided event ID
                    eventId = eventIdInput;
                    updateStatus(`Using existing event: ${eventId}`, 'info');
                } else {
                    // Create a new event
                    updateStatus('Creating new event...', 'warning');
                    const eventResponse = await fetch(`${API_BASE_URL}/mcp/execute`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            tool: 'events.create_event',
                            arguments: {
                                event_type: 'individual_practice',
                                event_name: 'Browser Recording Test Event',
                                description: 'Test event created from browser recording',
                                max_participants: 1,
                                duration_minutes: 10
                            }
                        })
                    });
                    
                    const eventData = await eventResponse.json();
                    if (eventData.error) {
                        throw new Error(`Event creation failed: ${eventData.error}`);
                    }
                    
                    eventId = eventData.event_id;
                    updateStatus(`Event created: ${eventId}`, 'info');
                }
                
                // Step 2: Start recording session
                updateStatus('Starting recording session...', 'warning');
                const sessionResponse = await fetch(`${API_BASE_URL}/mcp/execute`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        tool: 'pitches.start_recording',
                        arguments: {
                            event_id: eventId,
                            team_name: teamName,
                            pitch_title: pitchTitle
                        }
                    })
                });
                
                const sessionData = await sessionResponse.json();
                if (sessionData.error) {
                    throw new Error(`Session creation failed: ${sessionData.error}`);
                }
                
                const sessionId = sessionData.session_id;
                updateStatus(`Recording session created: ${sessionId}`, 'info');
                
                // Step 3: Send raw WebM to backend for proper FFmpeg conversion
                updateStatus('🔧 Sending raw WebM audio to backend for FFmpeg conversion...', 'warning');
                
                // Send the original WebM blob directly (bypass broken JS conversion)
                const webmReader = new FileReader();
                webmReader.onload = async () => {
                    try {
                        const base64WebM = webmReader.result.split(',')[1]; // Remove data: prefix
                        
                        const stopResponse = await fetch(`${API_BASE_URL}/mcp/execute`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                tool: 'pitches.stop_recording',
                                arguments: {
                                    session_id: sessionId,
                                    audio_data_base64: base64WebM,
                                    audio_format: 'webm'  // Tell backend this is WebM
                                }
                            })
                        });
                        
                        const stopData = await stopResponse.json();
                        if (stopData.error) {
                            throw new Error(`Upload failed: ${stopData.error}`);
                        }
                        
                        // Step 5: Get playback URL
                        updateStatus('Generating playback URL...', 'warning');
                        const playbackResponse = await fetch(`${API_BASE_URL}/mcp/execute`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                tool: 'pitches.get_playback_url',
                                arguments: {
                                    session_id: sessionId,
                                    expires_hours: 24
                                }
                            })
                        });
                        
                        const playbackData = await playbackResponse.json();
                        
                        // Display results
                        const sessionInfo = document.getElementById('sessionInfo');
                        
                        // Check for transcript
                        let transcriptHtml = '';
                        const transcript = stopData.transcript;
                        if (transcript) {
                            const totalText = transcript.total_text || '';
                            const segmentCount = transcript.segments_count || 0;
                            const segments = transcript.segments || [];
                            
                            if (totalText.trim()) {
                                // Calculate average confidence
                                let avgConfidence = 0;
                                let confidenceCount = 0;
                                let qualityWarning = '';
                                
                                segments.forEach(seg => {
                                    if (seg.confidence !== undefined) {
                                        avgConfidence += seg.confidence;
                                        confidenceCount++;
                                    }
                                });
                                
                                if (confidenceCount > 0) {
                                    avgConfidence = avgConfidence / confidenceCount;
                                    
                                    if (avgConfidence < 0.3) {
                                        qualityWarning = '<div style="background: #f8d7da; color: #721c24; padding: 10px; border-radius: 5px; margin: 10px 0;">⚠️ <strong>Very Low Quality:</strong> Transcript may be inaccurate. Try speaking louder and closer to the microphone.</div>';
                                    } else if (avgConfidence < 0.6) {
                                        qualityWarning = '<div style="background: #fff3cd; color: #856404; padding: 10px; border-radius: 5px; margin: 10px 0;">⚠️ <strong>Low Quality:</strong> Consider improving audio quality for better accuracy.</div>';
                                    } else {
                                        qualityWarning = '<div style="background: #d4edda; color: #155724; padding: 10px; border-radius: 5px; margin: 10px 0;">✅ <strong>Good Quality:</strong> Transcript should be accurate.</div>';
                                    }
                                }
                                
                                let segmentDetails = '';
                                if (segments.length > 0) {
                                    segmentDetails = '<h5>Segment Details:</h5>';
                                    segments.forEach((seg, i) => {
                                        const conf = seg.confidence !== undefined ? (seg.confidence * 100).toFixed(0) + '%' : 'N/A';
                                        const confColor = seg.confidence < 0.3 ? '#e74c3c' : seg.confidence < 0.6 ? '#f39c12' : '#27ae60';
                                        segmentDetails += `<div style="margin: 5px 0; padding: 8px; background: #f8f9fa; border-radius: 3px;"><strong>"${seg.text}"</strong> <span style="color: ${confColor}; font-weight: bold;">(${conf})</span></div>`;
                                    });
                                }
                                
                                transcriptHtml = `
                                    <h4>📝 Transcript</h4>
                                    <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0;">
                                        <strong>"${totalText}"</strong>
                                    </div>
                                    ${qualityWarning}
                                    <p><small>Segments: ${segmentCount} | Avg. Confidence: ${confidenceCount > 0 ? (avgConfidence * 100).toFixed(0) + '%' : 'N/A'}</small></p>
                                    ${segmentDetails}
                                `;
                            } else if (segmentCount > 0) {
                                transcriptHtml = `
                                    <h4>📝 Transcript</h4>
                                    <p><em>Processing completed but no text detected (${segmentCount} segments processed)</em></p>
                                `;
                            } else {
                                transcriptHtml = `
                                    <h4>📝 Transcript</h4>
                                    <p><em>No transcript segments detected - this may happen with synthetic audio or background noise</em></p>
                                `;
                            }
                        }
                        
                        // Debug: Log the full response for analysis
                        console.log('🔍 Full stopData response:', stopData);
                        console.log('🔍 Transcript object:', transcript);
                        if (transcript && transcript.segments) {
                            console.log('🔍 Individual segments:', transcript.segments);
                        }
                        
                        sessionInfo.innerHTML = `
                            <h4>✅ Upload Successful!</h4>
                            <p><strong>Session ID:</strong> ${sessionId}</p>
                            <p><strong>Event ID:</strong> ${eventId}</p>
                            <p><strong>Team:</strong> ${teamName}</p>
                            <p><strong>Title:</strong> ${pitchTitle}</p>
                            <p><strong>Status:</strong> ${stopData.status}</p>
                            <p><strong>File Size:</strong> ${Math.round(recordedBlob.size / 1024)}KB (WebM → WAV via FFmpeg)</p>
                            <p><strong>Processing Method:</strong> ${stopData.processing_method || 'WebSocket API (FFmpeg)'}</p>
                            ${transcriptHtml}
                        `;
                        
                        // Display playback URL - check both stopData and playbackData
                        const playbackUrl = document.getElementById('playbackUrl');
                        let audioUrl = null;
                        
                        // First try to get URL from stopData (more reliable)
                        if (stopData.audio && stopData.audio.playback_url) {
                            audioUrl = stopData.audio.playback_url;
                        } else if (playbackData && playbackData.playback_url) {
                            audioUrl = playbackData.playback_url;
                        }
                        
                        if (audioUrl) {
                            playbackUrl.innerHTML = `
                                <h4>🔗 MinIO Playback URL:</h4>
                                <div class="playback-url">${audioUrl}</div>
                                <p><small>This URL expires in 24 hours</small></p>
                                <audio controls class="audio-player">
                                    <source src="${audioUrl}" type="audio/wav">
                                    Your browser does not support the audio element.
                                </audio>
                            `;
                        } else {
                            playbackUrl.innerHTML = '<p>⚠️ No playback URL available</p>';
                        }
                        
                        updateStatus('🎉 Recording successfully processed with FFmpeg and uploaded!', 'info');
                        
                    } catch (innerError) {
                        updateStatus(`Processing failed: ${innerError.message}`, 'error');
                        console.error('Processing error:', innerError);
                        uploadBtn.disabled = false;
                    }
                };
                
                // Start reading the WebM blob as base64
                webmReader.readAsDataURL(recordedBlob);
                
            } catch (error) {
                updateStatus(`Upload failed: ${error.message}`, 'error');
                console.error('Upload error:', error);
                uploadBtn.disabled = false;
            }
        }