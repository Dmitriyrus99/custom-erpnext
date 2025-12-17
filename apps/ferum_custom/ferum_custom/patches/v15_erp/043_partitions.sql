-- Partition helpers (only if parents are partitioned)
DO $$
DECLARE y int; m int; from_d date; to_d date; part text; parent_exists bool; BEGIN
  -- Invoice partitions
  SELECT EXISTS (
    SELECT 1 FROM pg_partitioned_table p JOIN pg_class c ON p.partrelid = c.oid WHERE c.relname='tabInvoice'
  ) INTO parent_exists;
  IF parent_exists THEN
    FOR y IN 2022..2025 LOOP
      FOR m IN 1..12 LOOP
        from_d := make_date(y,m,1);
        to_d   := (from_d + INTERVAL '1 month')::date;
        part := format('tabInvoice_%s_%s', y, lpad(m::text,2,'0'));
        EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF tabInvoice FOR VALUES FROM (%L) TO (%L);', part, from_d, to_d);
      END LOOP;
    END LOOP;
  END IF;

  -- Payment partitions
  SELECT EXISTS (
    SELECT 1 FROM pg_partitioned_table p JOIN pg_class c ON p.partrelid = c.oid WHERE c.relname='tabPayment'
  ) INTO parent_exists;
  IF parent_exists THEN
    FOR y IN 2022..2025 LOOP
      FOR m IN 1..12 LOOP
        from_d := make_date(y,m,1);
        to_d   := (from_d + INTERVAL '1 month')::date;
        part := format('tabPayment_%s_%s', y, lpad(m::text,2,'0'));
        EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF tabPayment FOR VALUES FROM (%L) TO (%L);', part, from_d, to_d);
      END LOOP;
    END LOOP;
  END IF;
END$$;
