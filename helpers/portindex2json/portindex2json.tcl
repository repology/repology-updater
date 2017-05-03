# Script for converting the metadata in the PortIndex to 
# a list of JSON objects.
# Written by Joshua Root <jmr@macports.org>, 2017
# Requires: tclsh with the tcllib 'json' package.
# Usage: tclsh portindex2json.tcl < path/to/PortIndex

# To the extent possible under law, the author(s) have dedicated all
# copyright and related and neighboring rights to this software to the
# public domain worldwide. This software is distributed without any
# warranty.
# <https://creativecommons.org/publicdomain/zero/1.0/>

package require json::write

set fd stdin
while {[gets $fd line] >= 0} {
    if {[llength $line] != 2} {
        continue
    }
    set len [lindex $line 1]
    set line [read $fd $len]
    array unset portinfo
    array set portinfo $line
    array unset json_portinfo
    foreach key [array names portinfo] {
        set json_portinfo($key) [::json::write string $portinfo($key)]
    }
    lappend objects [::json::write object {*}[array get json_portinfo]]
}
puts [::json::write array {*}$objects]
