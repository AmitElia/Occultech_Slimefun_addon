package io.github.amitelia.occultech.event;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

class RaidGeometryTest {

    @Test
    void aLowRingIsJumpedOver() {
        assertTrue(RaidGeometry.ringHits(5, 0, 0, 5, 0.6, RaidRing.LOW, Double.NaN, 1.6), "standing on it");
        assertFalse(RaidGeometry.ringHits(5, 0, 1.0, 5, 0.6, RaidRing.LOW, Double.NaN, 1.6), "mid-jump");
        assertFalse(RaidGeometry.ringHits(7, 0, 0, 5, 0.6, RaidRing.LOW, Double.NaN, 1.6), "not there yet");
        assertFalse(RaidGeometry.ringHits(3, 0, 0, 5, 0.6, RaidRing.LOW, Double.NaN, 1.6), "already passed");
    }

    @Test
    void aTallRingIsWalkedThroughItsGap() {
        double gap = Math.PI / 2;   // toward +z
        assertTrue(RaidGeometry.ringHits(5, 0, 1.2, 5, 0.6, RaidRing.TALL, gap, 1.6), "jumping doesn't clear it");
        assertFalse(RaidGeometry.ringHits(0, 5, 0, 5, 0.6, RaidRing.TALL, gap, 1.6), "in the gap");
        assertFalse(RaidGeometry.ringHits(1.2, 4.85, 0, 5, 0.6, RaidRing.TALL, gap, 1.6), "near the gap's middle");
        assertTrue(RaidGeometry.ringHits(3.5, 3.57, 0, 5, 0.6, RaidRing.TALL, gap, 1.6), "past the gap's edge");
        // the gap is as wide in blocks far out as close in
        assertFalse(RaidGeometry.ringHits(1.4, 11.9, 0, 12, 0.6, RaidRing.TALL, gap, 1.6));
    }

    @Test
    void anglesWrapAround() {
        assertEquals(0.2, RaidGeometry.angleBetween(Math.PI - 0.1, -Math.PI + 0.1) * -1, 1e-9);
        assertEquals(-0.5, RaidGeometry.angleBetween(0.5, 1.0), 1e-9);
    }

    @Test
    void wallsPushBackToYourOwnSide() {
        // wall along x from (0,0) to (10,0)
        double[] north = RaidGeometry.fromWall(5, -0.3, 0, 0, 10, 0);
        assertEquals(0.3, north[0], 1e-9);
        assertEquals(-1, north[2], 1e-9);
        double[] south = RaidGeometry.fromWall(5, 0.4, 0, 0, 10, 0);
        assertEquals(1, south[2], 1e-9);
        double[] pastEnd = RaidGeometry.fromWall(12, 0, 0, 0, 10, 0);
        assertEquals(2, pastEnd[0], 1e-9);
        assertEquals(1, pastEnd[1], 1e-9);
        double[] onIt = RaidGeometry.fromWall(5, 0, 0, 0, 10, 0);
        assertEquals(0, onIt[0], 1e-9);
        assertEquals(1, Math.hypot(onIt[1], onIt[2]), 1e-9, "still a direction to push");
    }

    @Test
    void aBarrierIsPassedThroughItsGap() {
        // the line is at along = 0, the gap spans across 3..7
        assertTrue(RaidGeometry.barrierHits(0.2, 0, 5, 2, 0.7, 20), "on the line, away from the gap");
        assertFalse(RaidGeometry.barrierHits(0.2, 5, 5, 2, 0.7, 20), "in the gap");
        assertFalse(RaidGeometry.barrierHits(1.5, 0, 5, 2, 0.7, 20), "not reached yet");
        assertFalse(RaidGeometry.barrierHits(0, 21, 5, 2, 0.7, 20), "past its end");
    }

    @Test
    void aLowBeamIsJumpedAndAFullOneHasAGap() {
        // beam along +x
        assertTrue(RaidGeometry.laserHits(5, 0.3, 0, 0, 0.5, 12, SpinningLaser.LOW, Double.NaN, Double.NaN));
        assertFalse(RaidGeometry.laserHits(5, 0.3, 1, 0, 0.5, 12, SpinningLaser.LOW, Double.NaN, Double.NaN), "jumped");
        assertFalse(RaidGeometry.laserHits(5, 2, 0, 0, 0.5, 12, SpinningLaser.LOW, Double.NaN, Double.NaN), "beside it");
        assertFalse(RaidGeometry.laserHits(-5, 0, 0, 0, 0.5, 12, SpinningLaser.LOW, Double.NaN, Double.NaN), "behind the pivot");
        assertFalse(RaidGeometry.laserHits(13, 0, 0, 0, 0.5, 12, SpinningLaser.LOW, Double.NaN, Double.NaN), "out of reach");
        assertTrue(RaidGeometry.laserHits(3, 0, 1.2, 0, 0.5, 12, SpinningLaser.FULL, 5, 7.5), "too tall to jump");
        assertFalse(RaidGeometry.laserHits(6, 0, 0, 0, 0.5, 12, SpinningLaser.FULL, 5, 7.5), "standing in its gap");
    }

    @Test
    void soakingSplitsTheHit() {
        assertEquals(20, RaidGeometry.soakShare(5, 5, 20, 42), 1e-9, "enough people: each takes one share");
        assertEquals(10, RaidGeometry.soakShare(5, 10, 20, 42), 1e-9, "more people: less each");
        assertEquals(33.333, RaidGeometry.soakShare(5, 3, 20, 42), 1e-3, "too few: more each");
        assertEquals(42, RaidGeometry.soakShare(5, 1, 20, 42), 1e-9, "alone: capped");
        assertEquals(0, RaidGeometry.soakShare(5, 0, 20, 42), 1e-9);
    }
}
