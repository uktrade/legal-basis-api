web: waitress-serve --ident='' --listen=0.0.0.0:$PORT --threads=${WEB_CONCURRENCY:-4} --trusted-proxy '*' --trusted-proxy-headers 'x-forwarded-proto' server.wsgi:application
formsapi_poller: ./manage.py poll_formsapi --forever
dynamics_poller: ./manage.py poll_dynamics --forever --sleep-time 86400
