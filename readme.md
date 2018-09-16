# LongSphinx, aka Tim the Diviner

## Implemented commands:

* !hello
    * Debug message, responds with a "hello" and mentions the requester.
* !role <rolename>
    * Changes the requester to <rolename>, with all secondary roles, if <rolename> is in the list of valid roles for the server.
* !list
    * Lists the available roles.
* !name
    * Generates a random fantasy name.
* !roll <dice string>
    * Rolls dice. Syntax: !roll 1d20 2d4 will roll a twenty-sided die and two four-sided dice and give you the results in order, with the sum at the end.

## "Undocumented" commands

Any function listed here is unsupported, not guaranteed to stay past any given future update, and potentially buggy.

* &join
    * Simulates the requester joining, giving them a new random role.
