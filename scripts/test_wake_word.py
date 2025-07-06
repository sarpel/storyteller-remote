#!/usr/bin/env python3
"""
StorytellerPi Wake Word Testing Script (Python)
Simulates wake word detection for testing purposes
"""

import os
import sys
import time
import argparse
import logging
from pathlib import Path

# Add the main directory to path for imports
sys.path.append(str(Path(__file__).parent.parent / 'main'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[WAKE-TEST] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

class WakeWordTester:
    """Wake word testing utility"""
    
    def __init__(self):
        self.trigger_file = "/tmp/storyteller_wake_trigger"
        self.testing_active = False
        
    def check_testing_mode(self):
        """Check if testing mode is active"""
        if not os.path.exists(self.trigger_file):
            logger.error("Testing mode not active or StorytellerPi not running")
            logger.info("Make sure:")
            logger.info("1. StorytellerPi is running")
            logger.info("2. WAKE_WORD_TESTING_MODE=true in .env file")
            logger.info("3. Service has been restarted after configuration change")
            return False
        
        # Check if it's a FIFO pipe
        import stat
        if not stat.S_ISFIFO(os.stat(self.trigger_file).st_mode):
            logger.error("Trigger file exists but is not a FIFO pipe")
            return False
        
        self.testing_active = True
        return True
    
    def trigger_wake_word(self, confidence=1.0, wake_word="hey_elsa", verbose=False):
        """Trigger wake word detection"""
        if not self.check_testing_mode():
            return False
        
        if verbose:
            logger.info(f"Triggering wake word detection...")
            logger.info(f"Wake word: {wake_word}")
            logger.info(f"Confidence: {confidence}")
        
        try:
            with open(self.trigger_file, 'w') as f:
                f.write(f'WAKE {confidence} {wake_word}\n')
            
            logger.info("Wake word triggered successfully!")
            if verbose:
                logger.info("Check StorytellerPi logs for detection confirmation")
            return True
            
        except Exception as e:
            logger.error(f"Failed to trigger wake word: {e}")
            return False
    
    def show_status(self):
        """Show testing mode status"""
        logger.info("Checking StorytellerPi testing mode status...")
        
        if os.path.exists(self.trigger_file):
            import stat
            file_stat = os.stat(self.trigger_file)
            
            if stat.S_ISFIFO(file_stat.st_mode):
                logger.info("✅ Testing mode is ACTIVE")
                logger.info(f"Trigger file: {self.trigger_file}")
                logger.info("You can trigger wake word detection using this script")
                
                # Show file permissions
                perms = oct(file_stat.st_mode)[-3:]
                logger.info(f"File permissions: {perms}")
                
                return True
            else:
                logger.warning("Trigger file exists but is not a FIFO pipe")
                return False
        else:
            logger.warning("Testing mode is INACTIVE")
            logger.info("To enable testing mode:")
            logger.info("1. Add WAKE_WORD_TESTING_MODE=true to .env file")
            logger.info("2. Restart StorytellerPi service")
            return False
    
    def interactive_mode(self):
        """Interactive testing mode"""
        logger.info("Starting interactive wake word testing mode")
        logger.info("Commands: trigger, custom <word>, confidence <val>, status, quit")
        
        if not self.check_testing_mode():
            return
        
        confidence = 1.0
        wake_word = "hey_elsa"
        
        while True:
            try:
                cmd = input("\nwake-test> ").strip().lower()
                
                if not cmd:
                    continue
                elif cmd == 'quit' or cmd == 'exit':
                    break
                elif cmd == 'trigger':
                    self.trigger_wake_word(confidence, wake_word, verbose=True)
                elif cmd.startswith('custom '):
                    wake_word = cmd.split(' ', 1)[1]
                    logger.info(f"Wake word set to: {wake_word}")
                elif cmd.startswith('confidence '):
                    try:
                        confidence = float(cmd.split(' ', 1)[1])
                        if 0.0 <= confidence <= 1.0:
                            logger.info(f"Confidence set to: {confidence}")
                        else:
                            logger.error("Confidence must be between 0.0 and 1.0")
                    except ValueError:
                        logger.error("Invalid confidence value")
                elif cmd == 'status':
                    self.show_status()
                elif cmd == 'help':
                    print("\nAvailable commands:")
                    print("  trigger              - Trigger wake word with current settings")
                    print("  custom <word>        - Set custom wake word")
                    print("  confidence <val>     - Set confidence level (0.0-1.0)")
                    print("  status               - Show testing mode status")
                    print("  help                 - Show this help")
                    print("  quit/exit            - Exit interactive mode")
                    print(f"\nCurrent settings: word='{wake_word}', confidence={confidence}")
                else:
                    logger.error(f"Unknown command: {cmd}")
                    
            except KeyboardInterrupt:
                break
            except EOFError:
                break
        
        logger.info("Interactive mode ended")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="StorytellerPi Wake Word Testing Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                              # Simple wake word trigger
  %(prog)s --word "hello" --confidence 0.8  # Custom word and confidence
  %(prog)s --status                     # Check testing mode status
  %(prog)s --interactive                # Interactive mode
  %(prog)s --batch 5                    # Trigger 5 times with delay

Notes:
  - Testing mode must be enabled in StorytellerPi configuration
  - Set WAKE_WORD_TESTING_MODE=true in .env file
  - This script is for TESTING PURPOSES ONLY
        """
    )
    
    parser.add_argument(
        '-w', '--word',
        default='hey_elsa',
        help='Wake word to trigger (default: hey_elsa)'
    )
    
    parser.add_argument(
        '-c', '--confidence',
        type=float,
        default=1.0,
        help='Confidence level (0.0-1.0, default: 1.0)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Quiet mode (errors only)'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show testing mode status'
    )
    
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Interactive testing mode'
    )
    
    parser.add_argument(
        '--batch',
        type=int,
        metavar='N',
        help='Trigger N times with 2-second delay'
    )
    
    parser.add_argument(
        '--delay',
        type=float,
        default=2.0,
        help='Delay between batch triggers (default: 2.0 seconds)'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    elif args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate confidence
    if not 0.0 <= args.confidence <= 1.0:
        logger.error("Confidence must be between 0.0 and 1.0")
        sys.exit(1)
    
    # Create tester
    tester = WakeWordTester()
    
    # Execute command
    if args.status:
        success = tester.show_status()
        sys.exit(0 if success else 1)
    
    elif args.interactive:
        tester.interactive_mode()
    
    elif args.batch:
        logger.info(f"Batch mode: triggering {args.batch} times with {args.delay}s delay")
        
        success_count = 0
        for i in range(args.batch):
            logger.info(f"Trigger {i+1}/{args.batch}")
            
            if tester.trigger_wake_word(args.confidence, args.word, args.verbose):
                success_count += 1
            
            if i < args.batch - 1:  # Don't delay after last trigger
                time.sleep(args.delay)
        
        logger.info(f"Batch complete: {success_count}/{args.batch} successful")
        sys.exit(0 if success_count == args.batch else 1)
    
    else:
        # Single trigger
        success = tester.trigger_wake_word(args.confidence, args.word, args.verbose)
        sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()