#!/bin/sh
perl -I ~/perl5/lib/perl5/ ./term-replay-client term_trace_4 perl -I ~/perl5/lib/perl5/ ./term-replay-server term_trace_4 2> stderr
