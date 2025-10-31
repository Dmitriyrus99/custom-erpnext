
redis_cache: redis-server config/redis_cache.conf
redis_queue: redis-server config/redis_queue.conf


web: bench serve --port 8000 --noreload


socketio: node apps/frappe/socketio.js


watch: bench watch


schedule: bench schedule

worker-default: bench worker --queue default,short 1>> logs/worker-default.log 2>> logs/worker-default.error.log
worker-short:   bench worker --queue short 1>> logs/worker-short.log 2>> logs/worker-short.error.log
worker-long:    bench worker --queue long 1>> logs/worker-long.log 2>> logs/worker-long.error.log
