module.exports = {
    apps: [
        {
            name: 'plex',
            script: 'southpark.py',
            watch: false,
            autostart: false,
            interpreter: '/usr/bin/python3.8'
        }
    ]
};
