#!/usr/bin/env python3

import os
import json
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright, Page
from typing import List, Dict
import argparse
import re
import time

async def login_to_slack(page: Page, workspace_url: str, auth_file: str = "slack_auth.json") -> bool:
    """Log into Slack workspace."""
    try:
        print("Navigating to workspace...")
        await page.goto(workspace_url)
        
        # Check if we need to log in
        try:
            # Wait briefly to see if we're already logged in
            await page.wait_for_selector('[data-qa="top_nav_search"]', timeout=5000)
            print("Already logged in!")
            return True
        except:
            print("Need to log in...")
        
        # Wait for the login process
        print("Waiting for login (up to 2 minutes)...")
        print("Please log in through your browser...")
        
        # Wait for successful login
        try:
            # First wait for the client URL
            await page.wait_for_url("**/client/*", timeout=120000)
            
            # Then wait for the workspace to be fully loaded
            print("Logged in! Waiting for workspace to load...")
            await page.wait_for_selector('[data-qa="top_nav_search"]', timeout=30000)
            
            # Add a small delay to ensure everything is loaded
            await page.wait_for_timeout(5000)
            
            # Save authentication state
            print(f"Saving authentication state to {auth_file}")
            await page.context.storage_state(path=auth_file)
            
            return True
            
        except Exception as e:
            print(f"Login process failed: {str(e)}")
            return False
            
    except Exception as e:
        print(f"Login failed: {str(e)}")
        return False

async def navigate_to_search(page: Page, search_query: str):
    """Navigate to search results page."""
    try:
        # Wait for the workspace to fully load
        search_button = await page.wait_for_selector('[data-qa="top_nav_search"]', timeout=30000)
        
        if not search_button:
            raise Exception("Could not find search button")
            
        # Click the search box
        await search_button.click()
        await page.wait_for_timeout(2000)
        
        # Type the search query
        await page.keyboard.type(search_query)
        await page.wait_for_timeout(1000)
        await page.keyboard.press('Enter')
        
        print("Waiting for results to load...")
        await page.wait_for_selector('.c-search_message__content', timeout=30000)
        
        return True
        
    except Exception as e:
        print(f"Error during search: {str(e)}")
        return False

async def scroll_for_messages(page, exporter):
    """Scan for messages while gently scrolling."""
    processed_timestamps = set()
    expected_messages = 20
    no_new_messages_count = 0
    max_attempts_without_messages = 100  # With 100ms delay, this is 10 seconds
    
    print("\nScrolling gently and scanning for messages...")
    print(f"Looking for up to {expected_messages} messages\n")
    
    try:
        # Move mouse to middle of viewport for scrolling
        viewport_height = await page.evaluate('window.innerHeight')
        viewport_width = await page.evaluate('window.innerWidth')
        await page.mouse.move(viewport_width/2, viewport_height/2)
        
        while len(processed_timestamps) < expected_messages:
            prev_count = len(processed_timestamps)
            
            # Scan for messages
            groups = await page.query_selector_all('.c-message_group--ia4')
            for group in groups:
                timestamp_elem = await group.query_selector('a.c-timestamp')
                if timestamp_elem:
                    timestamp = await timestamp_elem.get_attribute('data-ts')
                    if timestamp and timestamp not in processed_timestamps:
                        processed_timestamps.add(timestamp)
                        # Extract and write message immediately
                        message_info = await extract_message_info(group)
                        if message_info:
                            exporter.write_message(message_info)
                            print(f"Found and saved message {len(processed_timestamps)} of {expected_messages}")
            
            # Check if we found any new messages
            if len(processed_timestamps) == prev_count:
                no_new_messages_count += 1
                if no_new_messages_count >= max_attempts_without_messages:
                    print(f"\nNo new messages found after {no_new_messages_count/10:.1f} seconds, assuming end of page")
                    break
            else:
                no_new_messages_count = 0
            
            # Gentle scroll using mouse wheel
            await page.mouse.wheel(0, 50)  # Small delta for gentle scrolling
            await page.wait_for_timeout(100)  # Brief pause to let content load
            
    except KeyboardInterrupt:
        print("\nStopped by user")
        return len(processed_timestamps)
    except Exception as e:
        print(f"Error during scan: {str(e)}")
        return len(processed_timestamps)
    
    print(f"\nTotal messages found: {len(processed_timestamps)}")
    return len(processed_timestamps)

async def navigate_to_next_page(page: Page) -> bool:
    """Navigate to the next page of results. Returns True if successful."""
    try:
        # Look for the next page button with multiple possible selectors
        next_button = await page.query_selector('[aria-label="Next page"], [data-qa="pagination_next"]')
        
        if not next_button:
            print("No next page button found")
            return False
            
        # Check if it's disabled
        is_disabled = await next_button.get_attribute('disabled') or await next_button.get_attribute('aria-disabled')
        if is_disabled:
            print("Next page button is disabled")
            return False
            
        print("Moving to next page...")
        await next_button.click()
        
        # Wait for new results to load
        await page.wait_for_selector('.c-search_message__content', timeout=30000)
        await page.wait_for_timeout(2000)  # Extra wait for stability
        
        return True
        
    except Exception as e:
        print(f"Error navigating to next page: {str(e)}")
        return False

async def extract_messages_from_page(page: Page):
    """Extract messages from the current page of search results."""
    try:
        # Wait for any loading to finish
        await wait_for_results_load(page)
        
        print("Processing page...")
        
        # Scroll to load all messages
        messages = await scroll_for_messages(page, None)
        
        # First get debug info about the page structure
        debug_info = await page.evaluate('''() => {
            // Get a sample message to understand structure
            const firstMsg = document.querySelector('.c-search_message__content');
            const structure = firstMsg ? {
                parentClasses: firstMsg.parentElement?.className || 'no parent',
                grandparentClasses: firstMsg.parentElement?.parentElement?.className || 'no grandparent',
                timeElement: {
                    exists: !!firstMsg.closest('.c-search_message--light')?.querySelector('time'),
                    classes: firstMsg.closest('.c-search_message--light')?.querySelector('time')?.className || 'no time element',
                    attributes: Array.from(firstMsg.closest('.c-search_message--light')?.querySelector('time')?.attributes || [])
                        .map(attr => `${attr.name}="${attr.value}"`)
                        .join(', ') || 'no attributes'
                },
                senderElement: {
                    exists: !!firstMsg.closest('.c-search_message--light')?.querySelector('.c-message__sender_button'),
                    classes: firstMsg.closest('.c-search_message--light')?.querySelector('.c-message__sender_button')?.className || 'no sender element'
                },
                textElement: {
                    exists: !!firstMsg.querySelector('.p-rich_text_section'),
                    classes: firstMsg.querySelector('.p-rich_text_section')?.className || 'no text element',
                    text: firstMsg.querySelector('.p-rich_text_section')?.textContent.trim() || 'no text'
                }
            } : 'No message found';
            
            return {
                structure,
                html: firstMsg?.parentElement?.outerHTML || 'no HTML'
            };
        }''')
        
        print("\nDOM Structure Analysis:")
        print(json.dumps(debug_info, indent=2))
        
        # Now extract messages
        messages_info = await page.evaluate('''() => {
            const messages = [];
            const messageElements = document.querySelectorAll('.c-search_message__content');
            console.log(`Found ${messageElements.length} message elements`);
            
            for (const msgElement of messageElements) {
                try {
                    // Get the parent message container
                    const parentMessage = msgElement.closest('.c-search_message--light');
                    if (!parentMessage) {
                        console.log('Skipping - no parent message found');
                        continue;
                    }
                    
                    // Get timestamp from the time element
                    const timeElement = parentMessage.querySelector('time');
                    let ts = null;
                    if (timeElement) {
                        // Try different timestamp attributes
                        ts = timeElement.getAttribute('data-ts');
                        const datetime = timeElement.getAttribute('datetime');
                        console.log('Timestamp info:', {
                            dataTs: ts,
                            datetime: datetime,
                            elementClasses: timeElement.className,
                            parentClasses: timeElement.parentElement?.className
                        });
                        
                        if (!ts && datetime) {
                            // Convert ISO datetime to Unix timestamp
                            try {
                                ts = (new Date(datetime).getTime() / 1000).toString();
                                console.log('Converted datetime to timestamp:', ts);
                            } catch (e) {
                                console.log('Failed to convert datetime:', e.message);
                            }
                        }
                    } else {
                        console.log('No time element found');
                    }
                    
                    // Get sender name
                    const senderElement = parentMessage.querySelector('.c-message__sender_button');
                    const sender = senderElement ? senderElement.textContent.trim() : 'Unknown';
                    console.log('Sender:', sender);
                    
                    // Get message text from rich text sections
                    const textElements = msgElement.querySelectorAll('.p-rich_text_section');
                    console.log(`Found ${textElements.length} text elements`);
                    let text = '';
                    for (const el of textElements) {
                        text += (text ? ' ' : '') + el.textContent.trim();
                    }
                    console.log('Message text:', text.substring(0, 100));
                    
                    // Only add if we have both timestamp and text
                    if (ts && text) {
                        messages.push({
                            sender: sender,
                            timestamp: ts,
                            text: text
                        });
                        console.log('Added message:', {
                            sender: sender,
                            timestamp: ts,
                            textPreview: text.substring(0, 50)
                        });
                    } else {
                        console.log('Skipping message - missing required fields:', {
                            hasTimestamp: !!ts,
                            timestampValue: ts,
                            hasText: !!text,
                            textLength: text.length
                        });
                    }
                } catch (e) {
                    console.error('Error processing message:', e.message);
                }
            }
            
            console.log(`Successfully extracted ${messages.length} messages`);
            return messages;
        }''')
        
        print(f"\nFound {len(messages_info)} messages on this page")
        return messages_info
        
    except Exception as e:
        print(f"Error extracting messages: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

async def get_total_results_count(page: Page) -> int:
    """Get the total number of search results."""
    try:
        # Try different selectors for the count
        count_selectors = [
            '[data-qa="search_result_header"] [data-qa="search_result_count"]',
            '[data-qa="search_result_count"]',
            '.p-search_results__count'
        ]
        
        for selector in count_selectors:
            try:
                count_element = await page.wait_for_selector(selector, timeout=5000)
                if count_element:
                    count_text = await count_element.text_content()
                    # Try to extract the number from text like "X results" or "X matches"
                    import re
                    if match := re.search(r'\d+', count_text):
                        return int(match.group())
            except:
                continue
        
        return 0
        
    except Exception as e:
        print(f"Error getting total count: {str(e)}")
        return 0

class SlackSearchExport:
    """Class to handle exporting Slack search results."""
    def __init__(self, output_file=None, output_format='text'):
        self.output_format = output_format
        self.total_messages = 0
        
        # Generate default filename if none provided
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.filename = f'slack_export_{timestamp}.txt'
        else:
            self.filename = output_file
            
        self.file = open(self.filename, 'w', encoding='utf-8')
        
        # Initialize JSON array if using JSON format
        if self.output_format == 'json':
            self.file.write('[\n')
            
    def write_message(self, message):
        """Write a single message to the output file."""
        try:
            if self.output_format == 'json':
                # Add comma if not first message
                if self.total_messages > 0:
                    self.file.write(',\n')
                json.dump(message, self.file, indent=2)
            else:
                # Text format: timestamp, sender, channel, text
                timestamp_str = datetime.fromtimestamp(message['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                channel = message.get('channel', 'unknown-channel')
                self.file.write(f"[{timestamp_str}] {message['sender']} in #{channel}:\n{message['text']}\n\n")
            
            self.total_messages += 1
            self.file.flush()  # Ensure message is written immediately
            
        except Exception as e:
            print(f"Error writing message: {e}")
            
    def close(self):
        """Finalize the file (especially important for JSON format)."""
        if self.output_format == 'json' and self.total_messages > 0:
            self.file.write('\n]')  # Close the JSON array
        self.file.flush()
        self.file.close()

async def extract_message_info(message_group):
    """Extract message information from a message group element."""
    try:
        # Find the message element within the group - it's inside the actions container
        message_element = await message_group.query_selector('.c-message_kit__actions .c-search_message')
        if not message_element:
            print("No message element found in group")
            return None
            
        # Get timestamp from the link element with class c-timestamp
        timestamp_element = await message_element.query_selector('.c-search_message__content a.c-timestamp')
        if not timestamp_element:
            print("No timestamp element found")
            return None
            
        # Get the data-ts attribute which contains the Unix timestamp
        timestamp = await timestamp_element.get_attribute('data-ts')
        if not timestamp:
            print("No timestamp attribute found")
            return None
            
        # Get sender from button with class c-message__sender_button
        sender_element = await message_element.query_selector('.c-search_message__content button.c-message__sender_button')
        if not sender_element:
            print("No sender element found")
            return None
        sender = await sender_element.text_content()
        
        # Get text content from p-rich_text_section
        text_element = await message_element.query_selector('.c-message__message_blocks .p-rich_text_section')
        if not text_element:
            print("No text element found")
            return None
        text = await text_element.text_content()
        
        # Get channel name from the message group header
        channel_element = await message_group.query_selector('.c-channel_entity__name')
        channel = None
        if channel_element:
            channel = await channel_element.text_content()
        else:
            # Fallback to extracting from timestamp URL if header not found
            href = await timestamp_element.get_attribute('href')
            if href:
                match = re.search(r'/archives/([^/]+)/', href)
                if match:
                    channel = match.group(1)

        return {
            'timestamp': float(timestamp),
            'sender': sender,
            'text': text,
            'channel': channel
        }
    except Exception as e:
        print(f"Error extracting message info: {e}")
        return None

async def process_message(page, message_group, exporter):
    """Process a single message."""
    try:
        # Extract message info using our helper function
        message_info = await extract_message_info(message_group)
        if message_info:
            exporter.write_message(message_info)
            
    except Exception as e:
        print(f"Error processing message: {e}")

async def process_messages(page, exporter):
    """Process messages from the current page."""
    try:
        # Wait for messages to load
        await page.wait_for_selector('.c-search_message', timeout=5000)
        
        # Scroll to load all messages
        messages = await scroll_for_messages(page, exporter)
        if not messages:
            print("No messages found on this page")
            return 0
            
        print(f"Found {len(messages)} messages")
        messages_processed = 0
        
        # Process each message
        for message_group in messages:
            # Extract message info using our helper function
            message_info = await extract_message_info(message_group)
            if message_info:
                exporter.write_message(message_info)
                messages_processed += 1
                
        print(f"Processed {messages_processed} messages")
        return messages_processed
        
    except Exception as e:
        print(f"Error processing messages: {str(e)}")
        return 0

async def process_search_results(page: Page, exporter: SlackSearchExport) -> int:
    """Process all pages of search results."""
    total_exported = 0
    page_num = 1
    
    while True:
        print(f"Processing page {page_num}...")
        messages = None
        try:
            messages = await scroll_for_messages(page, exporter)
        except KeyboardInterrupt:
            print("\nStopped by user")
            break
        except Exception as e:
            print(f"Error during scroll: {str(e)}")
            break

        if not await navigate_to_next_page(page):
            break
        
        page_num += 1
        await wait_for_results_load(page)
    
    return total_exported

async def main():
    parser = argparse.ArgumentParser(description='Slack Search and Export Tool')
    parser.add_argument('query', help='Search query to use')
    parser.add_argument('--workspace', help='Slack workspace URL', default='https://app.slack.com/client')
    parser.add_argument('--format', choices=['text', 'json'], default='text', help='Output format')
    parser.add_argument('--output', help='Output file (default: slack_export_[timestamp].txt)')
    parser.add_argument('--auth-file', default='slack_auth.json', help='Path to save/load authentication')
    
    args = parser.parse_args()
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(storage_state=args.auth_file if os.path.exists(args.auth_file) else None)
            page = await context.new_page()
            
            try:
                exporter = SlackSearchExport(args.output, args.format)
                
                if not await login_to_slack(page, args.workspace, args.auth_file):
                    print("Failed to log in to Slack")
                    return
                    
                print(f"Searching for: {args.query}")
                
                if not await navigate_to_search(page, args.query):
                    print("Failed to perform search")
                    return
                
                total_results = await get_total_results_count(page)
                if total_results > 0:
                    print(f"Found {total_results} total results")
                
                page_num = 1
                while True:
                    print(f"Processing page {page_num}...")
                    try:
                        messages_found = await scroll_for_messages(page, exporter)
                        if messages_found == 0:
                            print("No messages found on this page")
                        
                        if not await navigate_to_next_page(page):
                            break
                        
                        page_num += 1
                
                    except KeyboardInterrupt:
                        print("\nStopped by user")
                        break
                    
            except KeyboardInterrupt:
                print("\nStopped by user")
            finally:
                exporter.close()
                await browser.close()
                await context.close()
                
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nScript terminated by user")
