# Version 0.4.2

* Fixed exception being raised when command used in Private Message
* Display active channels if a PUG command is used in an inactive PUG Channel
* Renamed `about` command to `info`
* `promote` command can now be aliased with `p`
* Fixed no message being sent when idle captains are kicked

# Version 0.4.1

* Fix exception raised when accessing stats in last
* Don't display teams when showing pugstats without mod
* Don't store tags when saving teams
* Added `lastt`, `liastt`, `lasttt` and `liasttt` commands
* Added cooldown to promote command
* Switched to Pendulum date time library
* Allow captains to pick more than one player

# Version 0.4.0

* Refactored saving/loading stats
* If no mod is passed to `promote` or `fullreset` will default to mod if there is only one mod in the channel with players
* Reformatting for many of the messages
* Confirmation message for `setidlecaptaintimer`, `setrandcaptaintimer` and `setserver`
* Moderator commands
* `maplist` command for displaying a list of maps for each mod
* Better parsing for commands that expect a team mod
* `setpickmode` and `pickmode` commands
* `setlimit` command for setting the number of players required to fill a PUG
* `ut4` command sends link to Unreal Tournament home page if no subcommand is passed
* Allow `setserver` and `tag` to be used without quotes
* Truncate long tags
* Remove member's tags when they go offline
* tags are stored on a per server basis
* Admin commands for managing tags
* Remove server tags if a server is removed from the bot
* `leaveall` now removes members from all channels
* Escape Discord Markdown characters to prevent formatting
* Add an extra line between display current list and last when using `liast` command
* Remove unnecessary mod id when displaying last
* Print maps in sorted order

# Version 0.3.0

* Stats are stored separately, should improve performance when saving/loading stats
* Allow channels to set random/idle captains timer
* Explicit database opening for read/writes
* Don't display bans when showing PUG stats
* Limit the number of message editing when waiting for random captains
* Stats are store per channel, rather than per player
* top <n> commands added for puggers, captains, lamers and picks
* `active` command for displaying active channels in a server
* Players will be sent a DM if they are kicked for being idle
* Many of the PUG commands restricted to channels with active PUGChannel
* `invite` command can't be used inside DM
* `help` is context sensitive
* Custom parsing for mods

# Version 0.2.5

* Send small help messages to the channel it was requested
* If there is only one filled PUG when using reset, reset the PUG
* Cleaner formatting for players
* Fixed issue with random captains launching multiple coroutines
* Renamed `addplayer` to `addplayers`, now supports adding more than one player
* Formatting output
* When player leaves PUG, only DM if they were removed by a moderator
* When player leaves PUG, list the remaining players if there are any
* Promote PUG when player joins if only 1 or 2 players needed
* Remove idle players when they're selected as random captain

# Version 0.2.4

* Display available players after each pick
* Display available players after captains have been selected
* New separator when listing players and teams
* Display message when PUG has been reset with `fullreset`
* Notify users when they `leaveall` PUGs
* `purge` command for removing bot PMs
* Allow users to edit messages/commands

# Version 0.2.3

* `tag` command for appending a tag to users display name
* `nocaptain` command, removes member from being captain next PUG
* `nomic` command, appends 'nomic' to users display name when listing

# Version 0.2.2

* Unreal Tournament 4 related commands (changelog)
* Remove PUGChannel if associated channel is deleted
* Remove member from server PUGs when they leave a server
* Support more players (18) and more pickmodes

# Version 0.2.1

* `changelog` command (posts link to changelog on GitHub)
* Display current teams when using `.turn` command
* `teams` command now displays current teams, or teams from last PUG
* Randomly pick blue team captain based on average pick closest to red team captain

# Version 0.2.0

* Prettify output of list commands
* Countdown timer for random captains
* Display teams when listing if possible
* Notify members when they are selected as captain
* Remove members if they are banned (only removed from PUGs in the server they
were banned in)
