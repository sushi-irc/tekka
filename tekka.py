#!/usr/bin/env python
import tekka.main
import signal_handler

tekka.main.setup()
signal_handler.setup()

tekka.main.main()
