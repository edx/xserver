// require modules 
var 
 child_process = require('child_process');

var child = child_process.spawn('/usr/bin/sandbox', '-H /tmp/java -M sandbox50 env'.split(/\s+/), { 
 cwd: '/tmp/java',
 env: {
  PATH: [
   '/usr/local/bin',
   '/bin',
   '/usr/bin'
  ].join(':')
 }
});

child.stderr.on('data', function(data) {
    console.log(data.toString());
});

child.stdout.on('data', function(data) {
    console.log(data.toString());
});
