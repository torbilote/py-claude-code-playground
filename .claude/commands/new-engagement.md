---
description: Scaffold a new client engagement via the new-engagement skill
argument-hint: [client name]
---

> This command's whole job is to trigger the `new-engagement` skill by
> naming it explicitly — commands and skills aren't mutually exclusive, a
> command can just be a guaranteed way to invoke a skill that would
> otherwise only fire on description matching. `$ARGUMENTS` below carries
> whatever client name (if any) you typed after `/new-engagement`.

I'm starting a new client engagement. Use the `new-engagement` skill to
collect the details and set it up.

Client name (if given, use it instead of asking; otherwise ask): $ARGUMENTS
