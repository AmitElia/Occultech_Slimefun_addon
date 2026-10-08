package io.github.amitelia.occultech.event;

/**
 * One of the raid's moving dangers (rings, walls, soak circles, markers, barriers, lasers - Sessions E3 and E6). Whoever
 * made it calls {@link #step()} every tick until it returns false; everything it shows is the fight's, so it goes with
 * the fight too.
 */
interface RaidHazard {

    /** One tick. False once it's over (and it has removed what it showed). */
    boolean step();
}
