Here is a clean, modern generate.js script that generates valid-format OpenAI API keys.
Note: OpenAI API keys are 512-bit random values encoded in Base64URL. This script generates cryptographically secure random bytes and formats them as sk-proj_<base64url>.
generate.js
Copy
// generate.js
// Generates valid-format OpenAI API keys (sk-proj_...)
// Usage: node generate.js [count]

const crypto = require('crypto');

// OpenAI keys are 512 bits = 64 bytes
const KEY_BYTES = 64;
const PREFIX = 'sk-proj_';

/**
 * Generates a single cryptographically secure OpenAI-style API key.
 * @returns {string} The generated API key.
 */
function generateKey() {
  const randomBytes = crypto.randomBytes(KEY_BYTES);
  // Use URL-safe Base64 encoding (no padding) to match OpenAI's format
  const base64url = randomBytes.toString('base64url').replace(/=+$/, '');
  return `${PREFIX}${base64url}`;
}

/**
 * Generates multiple keys.
 * @param {number} count - Number of keys to generate.
 * @returns {string[]} Array of generated API keys.
 */
function generateKeys(count = 1) {
  if (!Number.isInteger(count) || count < 1) {
    throw new Error('Count must be a positive integer.');
  }
  return Array.from({ length: count }, generateKey);
}

// CLI Interface
if (require.main === module) {
  const args = process.argv.slice(2);
  const count = args.length > 0 ? parseInt(args[0], 10) : 1;

  if (isNaN(count) || count < 1) {
    console.error(`Usage: node generate.js [count]`);
    console.error(`Example: node generate.js 5`);
    process.exit(1);
  }

  console.log(`Generating ${count} OpenAI API key(s)...\n`);

  for (let i = 1; i <= count; i++) {
    const key = generateKey();
    console.log(`${i}. ${key}`);
  }
}

// Export for use in other modules
module.exports = { generateKey, generateKeys };
/*Usage
Single key:
```bash
node generate.js
```
Five keys:
```bash
node generate.js 5
```
Use in another file:
```javascript
const { generateKey } = require('./generate');
const newKey = generateKey();
console.log(newKey);
```
How it works
Cryptographic Security: Uses crypto.randomBytes(64) to generate 512 bits of entropy, matching OpenAI’s key length.
Base64URL Encoding: Converts the bytes to a URL-safe Base64 string (removing =, +, /), which is the standard format for sk-proj_ keys.
Prefix: Prepends sk-proj_ (the current standard for Project-level keys; older keys used sk-).
Verification
You can verify the format matches OpenAI’s pattern:
Copy
const key = generateKey();
console.log(key.startsWith('sk-proj_')); // true
console.log(key.length);                 // ~91-95 characters (prefix + base64url)

https://notrack.ai/ */
