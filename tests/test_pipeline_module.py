"""
Tests for the pipeline module functionality.
"""

import pytest

from pipeline import (
    BuildStage,
    LintStage,
    Pipeline,
    PipelineStage,
    PipelineTestStage,
    ScanStage,
    get_pipeline_status,
    run_pipeline,
    run_stage,
)


class TestPipelineStage:
    """Test the base PipelineStage class."""

    def test_stage_initialization(self):
        """Test that a stage initializes correctly."""
        stage = PipelineStage("test-stage")
        assert stage.name == "test-stage"
        assert stage.status == "pending"

    def test_stage_execution_success(self):
        """Test successful stage execution."""
        class MockStage(PipelineStage):
            def _run(self):
                return True

        stage = MockStage("mock")
        result = stage.execute()
        assert result is True
        assert stage.status == "success"

    def test_stage_execution_failure(self):
        """Test failed stage execution."""
        class MockStage(PipelineStage):
            def _run(self):
                return False

        stage = MockStage("mock")
        result = stage.execute()
        assert result is False
        assert stage.status == "failed"

    def test_stage_execution_error(self):
        """Test stage execution with exception."""
        class MockStage(PipelineStage):
            def _run(self):
                raise ValueError("Test error")

        stage = MockStage("mock")
        with pytest.raises(ValueError):
            stage.execute()
        assert stage.status == "error"

    def test_stage_abstract_method(self):
        """Test that _run method is abstract."""
        stage = PipelineStage("test")
        with pytest.raises(NotImplementedError):
            stage._run()


class TestSpecificStages:
    """Test specific pipeline stages."""

    def test_lint_stage(self):
        """Test LintStage initialization and execution."""
        stage = LintStage()
        assert stage.name == "lint"
        assert stage.status == "pending"

        result = stage.execute()
        assert result is True
        assert stage.status == "success"

    def test_test_stage(self):
        """Test PipelineTestStage initialization and execution."""
        stage = PipelineTestStage()
        assert stage.name == "test"
        assert stage.status == "pending"

        result = stage.execute()
        assert result is True
        assert stage.status == "success"

    def test_build_stage(self):
        """Test BuildStage initialization and execution."""
        stage = BuildStage()
        assert stage.name == "build"
        assert stage.status == "pending"

        result = stage.execute()
        assert result is True
        assert stage.status == "success"

    def test_scan_stage(self):
        """Test ScanStage initialization and execution."""
        stage = ScanStage()
        assert stage.name == "scan"
        assert stage.status == "pending"

        result = stage.execute()
        assert result is True
        assert stage.status == "success"


class TestPipeline:
    """Test the main Pipeline class."""

    def test_pipeline_initialization(self):
        """Test pipeline initializes with all stages."""
        pipeline = Pipeline()
        assert len(pipeline.stages) == 4

        stage_names = [stage.name for stage in pipeline.stages]
        assert "lint" in stage_names
        assert "test" in stage_names
        assert "build" in stage_names
        assert "scan" in stage_names

    def test_pipeline_run_all_stages(self):
        """Test running all pipeline stages."""
        pipeline = Pipeline()
        result = pipeline.run()
        assert result is True

        # Check all stages were executed
        for stage in pipeline.stages:
            assert stage.status == "success"

    def test_pipeline_run_specific_stage(self):
        """Test running a specific stage."""
        pipeline = Pipeline()
        result = pipeline.run("lint")
        assert result is True

        # Only lint stage should be executed
        lint_stage = next(s for s in pipeline.stages if s.name == "lint")
        assert lint_stage.status == "success"

        # Other stages should still be pending
        other_stages = [s for s in pipeline.stages if s.name != "lint"]
        for stage in other_stages:
            assert stage.status == "pending"

    def test_pipeline_run_invalid_stage(self):
        """Test running an invalid stage."""
        pipeline = Pipeline()
        with pytest.raises(ValueError, match="Unknown stage: invalid"):
            pipeline.run("invalid")

    def test_pipeline_get_status(self):
        """Test getting pipeline status."""
        pipeline = Pipeline()

        # Initial status
        status = pipeline.get_status()
        assert len(status) == 4
        for stage_name in ["lint", "test", "build", "scan"]:
            assert status[stage_name] == "pending"

        # After running one stage
        pipeline.run("test")
        status = pipeline.get_status()
        assert status["test"] == "success"
        assert status["lint"] == "pending"


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_run_pipeline_function(self):
        """Test run_pipeline convenience function."""
        result = run_pipeline()
        assert result is True

    def test_run_stage_function(self):
        """Test run_stage convenience function."""
        result = run_stage("lint")
        assert result is True

    def test_get_pipeline_status_function(self):
        """Test get_pipeline_status convenience function."""
        status = get_pipeline_status()
        assert isinstance(status, dict)
        assert len(status) == 4
        for stage_name in ["lint", "test", "build", "scan"]:
            assert stage_name in status


class TestPipelineIntegration:
    """Integration tests for the complete pipeline."""

    def test_full_pipeline_flow(self):
        """Test the complete pipeline flow."""
        pipeline = Pipeline()

        # Run individual stages in order
        stages = ["lint", "test", "build", "scan"]
        for stage_name in stages:
            result = pipeline.run(stage_name)
            assert result is True

            status = pipeline.get_status()
            assert status[stage_name] == "success"

    def test_pipeline_failure_propagation(self):
        """Test that pipeline stops on stage failure."""
        # Create a pipeline with a failing stage
        class FailingTestStage(PipelineTestStage):
            def _run(self):
                return False

        pipeline = Pipeline()
        # Replace test stage with failing one
        pipeline.stages[1] = FailingTestStage()

        # Run full pipeline - should fail at test stage
        result = pipeline.run()
        assert result is False

        status = pipeline.get_status()
        assert status["lint"] == "success"
        assert status["test"] == "failed"
        # Subsequent stages should not be executed
        assert status["build"] == "pending"
        assert status["scan"] == "pending"


# Mark tests for different categories
@pytest.mark.unit
class TestPipelineUnit:
    """Unit tests for pipeline components."""

    def test_stage_isolation(self):
        """Test that stages are isolated from each other."""
        stage1 = LintStage()
        stage2 = LintStage()

        stage1.execute()
        assert stage1.status == "success"
        assert stage2.status == "pending"  # Should not be affected


@pytest.mark.integration
class TestPipelineIntegrationMarked:
    """Integration tests marked for the pipeline."""

    def test_end_to_end_pipeline(self):
        """Test end-to-end pipeline execution."""
        result = run_pipeline()
        assert result is True

        # Note: get_pipeline_status() creates a new pipeline instance,
        # so it will show all stages as "pending" initially.
        # This tests that the function interface works correctly.
        status = get_pipeline_status()
        assert isinstance(status, dict)
        assert len(status) == 4
        for stage_name in ["lint", "test", "build", "scan"]:
            assert stage_name in status
