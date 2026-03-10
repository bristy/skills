const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const args = process.argv.slice(2);
const confirm = args.includes('--confirm');
const workspace = args.find(a => !a.startsWith('--'));

if (!confirm) {
    console.error("CRITICAL ERROR: This is a destructive operation that will overwrite files. You must explicitly pass the '--confirm' flag to proceed.");
    process.exit(1);
}

if (!workspace) {
    console.error("CRITICAL ERROR: Workspace path not provided. You must explicitly pass the target workspace path as an argument.");
    process.exit(1);
}

const filesToImport = [
    'MEMORY.md', 'IDENTITY.md', 'USER.md', 'SOUL.md', 'HEARTBEAT.md', 'AGENTS.md', 'TOOLS.md'
];

async function main() {
    console.log(`Starting legacy import for workspace: ${workspace}`);
    for (const file of filesToImport) {
        const fullPath = path.join(workspace, file);
        if (fs.existsSync(fullPath)) {
            const content = fs.readFileSync(fullPath, 'utf8');
            if (content.includes("migrated to SpacetimeDB")) {
                console.log(`Skipping ${file} - already migrated`);
                continue;
            }
            console.log(`Importing ${file}...`);
            
            // Create a backup before overwriting
            const backupPath = `${fullPath}.bak`;
            fs.copyFileSync(fullPath, backupPath);
            console.log(`Created backup at ${backupPath}`);

            const argsForStore = JSON.stringify({
                content: content.trim(),
                tags: ['legacy', 'import', file.replace('.md', '').toLowerCase()]
            });
            
            try {
                // Use execFileSync to prevent shell injection
                execFileSync(process.execPath, [
                    path.join(__dirname, 'tools/stdb_store.js'), 
                    argsForStore
                ], { stdio: 'inherit' });
                
                console.log(`Imported ${file}`);
                
                // Overwrite the file
                fs.writeFileSync(fullPath, `# ${file}\nContent migrated to SpacetimeDB. Use stdb_search.\n`);
            } catch (err) {
                console.error(`Failed to import ${file}: ${err.message}`);
            }
        }
    }
    console.log("Legacy import completed.");
}

main().catch(console.error);
