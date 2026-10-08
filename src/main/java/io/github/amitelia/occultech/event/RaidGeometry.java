package io.github.amitelia.occultech.event;

/**
 * The geometry behind the raid's shared hazards (Session E3, reused by Act 2): expanding rings you jump over or walk
 * through a gap in, and walls you can't cross. Pure Java, unit tested.
 */
public final class RaidGeometry {

    private RaidGeometry() {}

    /**
     * Whether an expanding ring catches a player standing at {@code (dx, dz)} from its center, {@code dy} above its base.
     *
     * @param radius       the ring's radius now
     * @param band         how thick the ring is (each side of the radius)
     * @param height       how tall it is: a player whose feet are this high or higher has jumped over it
     * @param gapAngle     the direction of the ring's gap (radians, as {@code atan2(dz, dx)}), or NaN for none
     * @param gapHalfWidth half the gap's width in blocks (measured along the ring, so it's the same at any radius)
     */
    public static boolean ringHits(double dx, double dz, double dy, double radius, double band, double height, double gapAngle,
        double gapHalfWidth) {
        double distance = Math.hypot(dx, dz);
        if (Math.abs(distance - radius) > band || dy >= height || dy < -1) {
            return false;
        }
        if (!Double.isNaN(gapAngle) && distance > 0.01) {
            double off = Math.abs(angleBetween(Math.atan2(dz, dx), gapAngle));
            if (off * distance <= gapHalfWidth) {
                return false;   // walked through the gap
            }
        }
        return true;
    }

    /**
     * Whether a sweeping barrier catches a player. The barrier is a line across the arena moving along its normal;
     * {@code along} is the player's distance from the line (along the movement), {@code across} their position along
     * the line from the arena's middle. The gap is {@code gapCenter +- gapHalfWidth} along the line.
     */
    public static boolean barrierHits(double along, double across, double gapCenter, double gapHalfWidth, double thickness, double halfLength) {
        return Math.abs(along) <= thickness && Math.abs(across) <= halfLength && Math.abs(across - gapCenter) > gapHalfWidth;
    }

    /**
     * Whether a spinning beam catches a player at {@code (dx, dz)} from its pivot, {@code dy} above it.
     *
     * @param beamAngle the beam's direction now (radians, as {@code atan2(dz, dx)})
     * @param halfWidth half the beam's width in blocks
     * @param height    a player whose feet are this high has jumped over it (a low beam); a full-height beam is taller than a jump
     * @param gapFrom   a full-height beam's safe stretch starts this far out (NaN: no gap)...
     * @param gapTo     ...and ends this far out
     */
    public static boolean laserHits(double dx, double dz, double dy, double beamAngle, double halfWidth, double length, double height,
        double gapFrom, double gapTo) {
        double distance = Math.hypot(dx, dz);
        if (distance < 0.5 || distance > length || dy >= height || dy < -1) {
            return false;
        }
        if (!Double.isNaN(gapFrom) && distance >= gapFrom && distance <= gapTo) {
            return false;
        }
        double off = Math.abs(angleBetween(Math.atan2(dz, dx), beamAngle));
        return off < Math.PI / 2 && Math.sin(off) * distance <= halfWidth;
    }

    /**
     * What each player standing in a soak circle takes: the circle's full damage is {@code needed x share}, split between
     * the {@code inside} players, but never more than {@code cap} each. Nobody inside: 0 (the caller hits the raid).
     */
    public static double soakShare(int needed, int inside, double share, double cap) {
        if (inside <= 0) {
            return 0;
        }
        return Math.min(cap, share * Math.max(1, needed) / inside);
    }

    /** The smallest signed difference {@code a - b} between two angles, in (-PI, PI]. */
    public static double angleBetween(double a, double b) {
        double d = (a - b) % (Math.PI * 2);
        if (d > Math.PI) {
            d -= Math.PI * 2;
        } else if (d <= -Math.PI) {
            d += Math.PI * 2;
        }
        return d;
    }

    /**
     * How a point {@code (px, pz)} stands to a wall from {@code (ax, az)} to {@code (bx, bz)}: {distance, nx, nz}, where
     * {@code (nx, nz)} is the unit direction from the wall's nearest point toward the point - the way to push someone who
     * touches it back to their own side. A point right on the wall gets the wall's left-hand normal.
     */
    public static double[] fromWall(double px, double pz, double ax, double az, double bx, double bz) {
        double wx = bx - ax;
        double wz = bz - az;
        double length2 = wx * wx + wz * wz;
        double t = length2 == 0 ? 0 : Math.max(0, Math.min(1, ((px - ax) * wx + (pz - az) * wz) / length2));
        double cx = ax + wx * t;
        double cz = az + wz * t;
        double ox = px - cx;
        double oz = pz - cz;
        double distance = Math.hypot(ox, oz);
        if (distance < 1e-6) {
            double length = Math.sqrt(length2);
            return length == 0 ? new double[] { 0, 1, 0 } : new double[] { 0, -wz / length, wx / length };
        }
        return new double[] { distance, ox / distance, oz / distance };
    }
}
