module.exports = {
    apps: [
        {
            name: 'plex',
            script: 'southpark.py',
            watch: false,
            autostart: false,
            interpreter: '/usr/bin/env python3.8'
        }
    ]
};
