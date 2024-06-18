FROM python:3.11.2-slim

RUN pip install --upgrade pip \
    && pip install --no-cache-dir \
    pyserial \
    requests

ENV PYTHONPATH=/usr/local/lib
COPY usr/local/lib/terminal_display_backend.py /usr/local/lib/terminal_display_backend.py
COPY usr/local/lib/terminal_display_widget.py /usr/local/lib/terminal_display_widget.py
COPY usr/local/lib/terminal_display_command.py /usr/local/lib/terminal_display_command.py
COPY usr/local/lib/terminal_display_serial.py /usr/local/lib/terminal_display_serial.py

# Use the mounted terminal-display.conf, do not include it in the container.
# RUN mkdir -p /etc/terminal-display
# COPY etc/terminal-display/terminal-display.conf /etc/terminal-display/terminal-display.conf

COPY usr/bin/terminal_display_client.py /usr/bin/terminal_display_client.py

CMD [ "terminal_display_client.py", "-f", "/etc/terminal-display/terminal-display.conf" ]
