#!/bin/sh
perl -I ~/perl5/lib/perl5/ ./term-replay-client term_trace_1 perl -I ~/perl5/lib/perl5/ ./term-replay-server term_trace_1 2> stderr
