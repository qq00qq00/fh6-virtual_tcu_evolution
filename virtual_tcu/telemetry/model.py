from dataclasses import dataclass

FH6_PACKET_SIZE = 324


@dataclass
class Telemetry:
    is_race_on: int = 0
    engine_max_rpm: float = 8000.0
    current_rpm: float = 0.0
    accel_x: float = 0.0
    accel_y: float = 0.0
    accel_z: float = 0.0
    vel_x: float = 0.0
    vel_y: float = 0.0
    vel_z: float = 0.0
    ang_vel_x: float = 0.0
    ang_vel_y: float = 0.0
    ang_vel_z: float = 0.0
    speed_ms: float = 0.0
    power_w: float = 0.0
    torque_nm: float = 0.0
    boost_raw: float = 0.0
    accel_raw: int = 0
    brake_raw: int = 0
    clutch_raw: int = 0
    gear: int = 0
    car_ordinal: int = 0
    car_class: int = 0
    pi: int = 0
    session_timestamp: int = 0
    idle_rpm: float = 0.0
    drivetrain: int = 0
    num_cylinders: int = 0
    slip_fl: float = 0.0
    slip_fr: float = 0.0
    slip_rl: float = 0.0
    slip_rr: float = 0.0
    is_shifting: bool = False

    @property
    def rear_slip(self) -> float:
        return max(abs(self.slip_rl), abs(self.slip_rr))

    @property
    def front_slip(self) -> float:
        return max(abs(self.slip_fl), abs(self.slip_fr))

    @property
    def speed_kmh(self) -> float:
        if 0.0 <= self.speed_ms < 200.0:
            return self.speed_ms * 3.6
        mag = (self.vel_x**2 + self.vel_y**2 + self.vel_z**2) ** 0.5
        return mag * 3.6

    @property
    def speed_effective_ms(self) -> float:
        if 0.0 <= self.speed_ms < 200.0:
            return self.speed_ms
        return (self.vel_x**2 + self.vel_y**2 + self.vel_z**2) ** 0.5

    @property
    def rpm_pct(self) -> float:
        return self.current_rpm / self.engine_max_rpm if self.engine_max_rpm > 0 else 0.0

    @property
    def throttle(self) -> float:
        return self.accel_raw / 255.0

    @property
    def brake(self) -> float:
        return self.brake_raw / 255.0

    @property
    def car_key(self) -> tuple[int, int, int]:
        """Composite vehicle identifier — distinct per car model *and* tune.

        ``car_ordinal`` alone is not enough: the same car with a different
        tune (gearing / engine swap / PI change) keeps the same ordinal,
        so the learning systems would silently reuse stale data.
        Including ``car_class`` and ``pi`` disambiguates tuned variants."""
        return (self.car_ordinal, self.car_class, self.pi)

    @property
    def drivetrain_name(self) -> str:
        return {0: "FWD", 1: "RWD", 2: "AWD"}.get(self.drivetrain, "—")
