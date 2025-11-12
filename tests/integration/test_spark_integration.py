"""
Integration tests for Spark cluster
Tests Spark job execution and data processing
"""

import pytest
from pyspark.sql import DataFrame
from pyspark.sql.functions import col, sum as spark_sum, avg, count


@pytest.mark.integration
@pytest.mark.smoke
class TestSparkCluster:
    """Test suite for Spark cluster integration"""

    def test_spark_session_active(self, spark_session):
        """Test that Spark session is active and connected"""
        assert spark_session is not None
        assert spark_session.sparkContext.master.startswith("spark://")
        print(f"Spark version: {spark_session.version}")

    def test_create_dataframe(self, spark_session, sample_data):
        """Test creating DataFrame from sample data"""
        df = spark_session.createDataFrame(sample_data["users"])
        assert df.count() == 5
        assert set(df.columns) == {"id", "name", "age", "city"}

    def test_basic_transformations(self, spark_session, sample_data):
        """Test basic Spark transformations"""
        df = spark_session.createDataFrame(sample_data["users"])

        # Filter
        filtered = df.filter(col("age") > 28)
        assert filtered.count() == 3

        # Select
        names = df.select("name").collect()
        assert len(names) == 5

        # OrderBy
        ordered = df.orderBy(col("age").desc())
        first_row = ordered.first()
        assert first_row["name"] == "Charlie"

    def test_aggregations(self, spark_session, sample_data):
        """Test Spark aggregation operations"""
        df = spark_session.createDataFrame(sample_data["users"])

        # Average age
        avg_age = df.agg(avg("age")).collect()[0][0]
        assert abs(avg_age - 30.0) < 0.1

        # Group by city
        city_counts = df.groupBy("city").count()
        assert city_counts.count() == 5

    def test_join_operations(self, spark_session, sample_data):
        """Test Spark join operations"""
        users_df = spark_session.createDataFrame(sample_data["users"])
        transactions_df = spark_session.createDataFrame(sample_data["transactions"])

        # Join users with transactions
        joined = users_df.join(
            transactions_df,
            users_df.id == transactions_df.user_id,
            "inner"
        )

        assert joined.count() == 5
        assert "name" in joined.columns
        assert "amount" in joined.columns

    def test_parallel_processing(self, spark_session):
        """Test parallel processing with multiple partitions"""
        # Create a larger dataset
        data = [(i, f"value_{i}") for i in range(1000)]
        df = spark_session.createDataFrame(data, ["id", "value"])

        # Repartition
        repartitioned = df.repartition(4)
        assert repartitioned.rdd.getNumPartitions() == 4

        # Process in parallel
        result = repartitioned.filter(col("id") % 2 == 0)
        assert result.count() == 500


@pytest.mark.integration
@pytest.mark.agent1
class TestDataIngestion:
    """Test suite for Agent 1: Data Ingestion"""

    def test_csv_ingestion(self, spark_session, tmp_path):
        """Test ingesting CSV data"""
        # Create test CSV
        csv_path = tmp_path / "test_data.csv"
        csv_path.write_text("id,name,value\n1,Alice,100\n2,Bob,200\n3,Charlie,300")

        # Ingest CSV
        df = spark_session.read.csv(str(csv_path), header=True, inferSchema=True)
        assert df.count() == 3
        assert "name" in df.columns

    def test_json_ingestion(self, spark_session, tmp_path):
        """Test ingesting JSON data"""
        import json

        # Create test JSON
        json_path = tmp_path / "test_data.json"
        data = [
            {"id": 1, "name": "Alice", "value": 100},
            {"id": 2, "name": "Bob", "value": 200}
        ]
        json_path.write_text("\n".join(json.dumps(d) for d in data))

        # Ingest JSON
        df = spark_session.read.json(str(json_path))
        assert df.count() == 2


@pytest.mark.integration
@pytest.mark.agent2
class TestDataProcessing:
    """Test suite for Agent 2: Data Processing"""

    def test_data_cleaning(self, spark_session):
        """Test data cleaning operations"""
        from pyspark.sql.functions import when, trim, upper

        # Create dirty data
        data = [
            (1, "  Alice  ", 30, None),
            (2, "Bob", None, "SF"),
            (3, None, 25, "NYC"),
            (4, "Charlie", 35, "Seattle")
        ]
        df = spark_session.createDataFrame(data, ["id", "name", "age", "city"])

        # Clean data
        cleaned = df.na.fill({"age": 0, "city": "Unknown"}) \
                     .withColumn("name", trim(col("name"))) \
                     .filter(col("name").isNotNull())

        assert cleaned.count() == 3

    def test_data_transformation(self, spark_session, sample_data):
        """Test data transformation pipeline"""
        from pyspark.sql.functions import when

        df = spark_session.createDataFrame(sample_data["users"])

        # Transform: add age category
        transformed = df.withColumn(
            "age_category",
            when(col("age") < 25, "young")
            .when(col("age") < 35, "adult")
            .otherwise("senior")
        )

        assert "age_category" in transformed.columns
        assert transformed.filter(col("age_category") == "adult").count() == 4


@pytest.mark.integration
@pytest.mark.agent6
class TestBatchProcessing:
    """Test suite for Agent 6: Batch Processing"""

    def test_batch_job_execution(self, spark_session, sample_data):
        """Test executing batch processing job"""
        df = spark_session.createDataFrame(sample_data["transactions"])

        # Batch aggregation
        result = df.groupBy("user_id").agg(
            spark_sum("amount").alias("total_amount"),
            count("*").alias("transaction_count")
        )

        assert result.count() == 3
        alice_total = result.filter(col("user_id") == 1).first()["total_amount"]
        assert abs(alice_total - 175.75) < 0.01

    def test_large_batch_processing(self, spark_session):
        """Test processing large batch of data"""
        # Generate large dataset
        data = [(i, i * 10, f"category_{i % 10}") for i in range(10000)]
        df = spark_session.createDataFrame(data, ["id", "value", "category"])

        # Process
        result = df.groupBy("category").agg(
            spark_sum("value").alias("total"),
            avg("value").alias("average")
        )

        assert result.count() == 10


@pytest.mark.integration
@pytest.mark.slow
class TestSparkPerformance:
    """Performance tests for Spark operations"""

    def test_large_dataset_processing(self, spark_session):
        """Test processing performance with large dataset"""
        import time

        # Create large dataset
        data = [(i, f"value_{i}", i * 2) for i in range(100000)]
        df = spark_session.createDataFrame(data, ["id", "name", "value"])

        # Measure processing time
        start = time.time()
        result = df.filter(col("id") % 2 == 0).count()
        duration = time.time() - start

        assert result == 50000
        assert duration < 10.0, f"Processing took {duration}s, expected < 10s"

    def test_multiple_stage_pipeline(self, spark_session, sample_data):
        """Test multi-stage processing pipeline"""
        users_df = spark_session.createDataFrame(sample_data["users"])
        transactions_df = spark_session.createDataFrame(sample_data["transactions"])

        # Multi-stage pipeline
        result = users_df.join(transactions_df, users_df.id == transactions_df.user_id) \
                        .groupBy("city") \
                        .agg(spark_sum("amount").alias("city_total")) \
                        .orderBy(col("city_total").desc())

        assert result.count() > 0
        assert "city_total" in result.columns
