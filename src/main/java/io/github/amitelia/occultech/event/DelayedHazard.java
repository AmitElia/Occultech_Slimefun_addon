package io.github.amitelia.occultech.event;

/** A hazard that starts a few ticks late (a stomp's second ring). */
final class DelayedHazard implements RaidHazard {

    private final RaidHazard hazard;
    private int wait;

    DelayedHazard(int delay, RaidHazard hazard) {
        this.wait = delay;
        this.hazard = hazard;
    }

    @Override
    public boolean step() {
        if (wait > 0) {
            wait--;
            return true;
        }
        return hazard.step();
    }
}
