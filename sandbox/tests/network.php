#!/bin/env php
<?php

    // this should work
    system("nslookup google.com");

    // this shouldn't
    system("wget http://www.google.com/ -O -");

?>
