## Simple Scaling
resource "aws_launch_template" "main" {
  name              = "launch-template-scaling-demo"
  image_id          = var.ami
  instance_type     = var.instanceType
  iam_instance_profile {
    arn = var.instanceProfile
  }
  instance_market_options {
    market_type = "spot"
  }
  credit_specification {
    cpu_credits = "standard"
  }
  tag_specifications {
    resource_type = "instance"
    tags = var.tags
  }
}

resource "aws_autoscaling_group" "simple" {
  name                 = "ASG-Simple"
  desired_capacity     = 1
  max_size             = 2
  min_size             = 1
  vpc_zone_identifier = [var.subnetsId[0], var.subnetsId[1]]
  launch_template {
    id      = aws_launch_template.main.id
    version = aws_launch_template.main.latest_version
  }
  health_check_type = "EC2"
  health_check_grace_period = 300
  default_instance_warmup = 300
  default_cooldown = 300
  capacity_rebalance = true
}

resource "aws_cloudwatch_metric_alarm" "cpu_scale_out" {
  alarm_name          = "SimpleScaling-CPUAlarmScaleOut"
  alarm_description   = "Alarm when CPU exceeds 50%"
  namespace           = "AWS/EC2"
  metric_name         = "CPUUtilization"
  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.simple.name
  }
  statistic           = "Average"
  period              = 300
  evaluation_periods   = 3
  threshold           = 50
  comparison_operator = "GreaterThanThreshold"
  alarm_actions       = [aws_autoscaling_policy.scale_out.arn]
  treat_missing_data  = "notBreaching"
}

resource "aws_cloudwatch_metric_alarm" "cpu_scale_in" {
  alarm_name          = "SimpleScaling-CPUAlarmScaleIn"
  alarm_description   = "Alarm when CPU below 50%"
  namespace           = "AWS/EC2"
  metric_name         = "CPUUtilization"
  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.simple.name
  }
  statistic           = "Average"
  period              = 300
  evaluation_periods   = 3
  threshold           = 50
  comparison_operator = "LessThanThreshold"
  alarm_actions       = [aws_autoscaling_policy.scale_in.arn]
  treat_missing_data  = "notBreaching"
}

resource "aws_autoscaling_policy" "scale_out" {
  name                   = "scale-out"
    adjustment_type        = "ExactCapacity"
  autoscaling_group_name = aws_autoscaling_group.simple.name
  scaling_adjustment      = 2
  policy_type            = "SimpleScaling"
}

resource "aws_autoscaling_policy" "scale_in" {
  name                   = "scale-in"
  adjustment_type        = "ExactCapacity"
  autoscaling_group_name = aws_autoscaling_group.simple.name
  scaling_adjustment      = 1
  policy_type            = "SimpleScaling"
}

## Step Scaling
resource "aws_autoscaling_group" "step" {
  name                 = "ASG-Step"
  desired_capacity     = 1
  max_size             = 4
  min_size             = 1
  vpc_zone_identifier = [var.subnetsId[0], var.subnetsId[1]]
  launch_template {
    id      = aws_launch_template.main.id
    version = aws_launch_template.main.latest_version
  }
  health_check_type = "EC2"
  health_check_grace_period = 300
  default_instance_warmup = 300
  default_cooldown = 300
  capacity_rebalance = true
}

resource "aws_cloudwatch_metric_alarm" "step_cpu_alarm" {
  alarm_name          = "StepScaling-AverageCPUAlarm"
  alarm_description   = "Alarm AvgCPUUtilization"
  namespace           = "AWS/EC2"
  metric_name         = "CPUUtilization"
  statistic           = "Average"
  period              = 300
  evaluation_periods   = 3
  threshold           = 25
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"

  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.step.name
  }

  alarm_actions = [
    aws_autoscaling_policy.step.arn
  ]
}

resource "aws_autoscaling_policy" "step" {
  name                   = "StepScaling"
  adjustment_type       = "ExactCapacity"
  autoscaling_group_name = aws_autoscaling_group.step.name
  policy_type           = "StepScaling"

  step_adjustment {
    metric_interval_lower_bound = 0
    metric_interval_upper_bound = 20
    scaling_adjustment          = 2
  }

  step_adjustment {
    metric_interval_lower_bound = 20
    metric_interval_upper_bound = 40
    scaling_adjustment          = 3
  }

  step_adjustment {
    metric_interval_lower_bound = 40
    scaling_adjustment          = 4
  }
}

## Target Tracking
resource "aws_autoscaling_group" "target-tracking" {
  name                 = "ASG-TargetTracking"
  desired_capacity     = 1
  max_size             = 2
  min_size             = 1
  vpc_zone_identifier = [var.subnetsId[0], var.subnetsId[1]]
  launch_template {
    id      = aws_launch_template.main.id
    version = aws_launch_template.main.latest_version
  }
  health_check_type = "EC2"
  health_check_grace_period = 300
  default_instance_warmup = 300
  default_cooldown = 300
  capacity_rebalance = true
}

resource "aws_autoscaling_policy" "target-tracking" {
  name                   = "TargetTrackingScalingPolicy"
  autoscaling_group_name = aws_autoscaling_group.target-tracking.name
  policy_type           = "TargetTrackingScaling"

  target_tracking_configuration {
    target_value = 50
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }
    disable_scale_in = false
  }
}